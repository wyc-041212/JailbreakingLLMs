from common import get_api_key, conv_template, extract_json
from language_models import APILiteLLM
from config import FASTCHAT_TEMPLATE_NAMES, Model
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_attack_and_target_models(args):
    # create attack model and target model
    attackLM = AttackLM(model_name = args.attack_model, 
                        max_n_tokens = args.attack_max_n_tokens, 
                        max_n_attack_attempts = args.max_n_attack_attempts, 
                        category = args.category,
                        evaluate_locally = args.evaluate_locally
                        )
    
    targetLM = TargetLM(model_name = args.target_model,
                        category = args.category,
                        max_n_tokens = args.target_max_n_tokens,
                        evaluate_locally = args.evaluate_locally,
                        use_jailbreakbench=args.use_jailbreakbench,
                        phase = args.jailbreakbench_phase
                        )
    
    return attackLM, targetLM

# def load_indiv_model(model_name, local = False, use_jailbreakbench=True):
def load_indiv_model(model_name, local = True, use_jailbreakbench=False):
    if use_jailbreakbench:
        if local:
            from jailbreakbench import LLMvLLM
            lm = LLMvLLM(model_name=model_name)
        else:
            from jailbreakbench import LLMLiteLLM
            api_key = get_api_key(Model(model_name))
            lm = LLMLiteLLM(model_name= model_name, api_key = api_key)
    else:
        if local:
            LOCAL_MODEL_PATHS = {
                "vicuna-13b-v1.5": "/home/comp/f2256768/JBShield/models/vicuna-13b-v1.5",
                "qwen-2.5-7b-instruct": "/home/comp/f2256768/JBShield/models/qwen-2.5-7b-instruct"
            }
            # raise NotImplementedError
            # ✅ 加上这个分支：支持本地 HF 模型加载
            class LocalHFWrapper:
                def __init__(self, model_name):
                    model_path = LOCAL_MODEL_PATHS[model_name]
                    # from config import QWEN_PATH  # 确保你已经在 config.py 里写了这个路径
                    self.model = AutoModelForCausalLM.from_pretrained(
                        # QWEN_PATH, torch_dtype=torch.float16, device_map="auto"
                        model_path, torch_dtype=torch.float16, device_map="auto"
                    )
                    # self.tokenizer = AutoTokenizer.from_pretrained(QWEN_PATH, use_fast=False)
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
                    self.tokenizer.chat_template = FASTCHAT_TEMPLATE_NAMES[Model(model_name)]
                    self.post_message = ""
                    # self.use_open_source_model = False
                    self.use_open_source_model = True

                def batched_generate(self, conversations, max_n_tokens, temperature, top_p, extra_eos_tokens=[]):
                    outputs = []
                    for conv in conversations:
                        input_text = self.tokenizer.apply_chat_template(conv, tokenize=False,
                                                                        add_generation_prompt=True)
                        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)
                        output = self.model.generate(
                            **inputs,
                            max_new_tokens=max_n_tokens,
                            do_sample=True,
                            temperature=temperature,
                            top_p=top_p,
                            eos_token_id=self.tokenizer.convert_tokens_to_ids(
                                extra_eos_tokens) if extra_eos_tokens else None
                        )
                        decoded = self.tokenizer.decode(output[0], skip_special_tokens=True)
                        outputs.append(decoded)
                    return outputs

            return LocalHFWrapper(model_name)
        else:
            lm = APILiteLLM(model_name)
    return lm

class AttackLM():
    """
        Base class for attacker language models.
        
        Generates attacks for conversations using a language model. The self.model attribute contains the underlying generation model.
    """
    def __init__(self, 
                model_name: str, 
                max_n_tokens: int, 
                max_n_attack_attempts: int, 
                category: str,
                evaluate_locally: bool):
        
        self.model_name = Model(model_name)
        self.max_n_tokens = max_n_tokens
        self.max_n_attack_attempts = max_n_attack_attempts

        from config import ATTACK_TEMP, ATTACK_TOP_P
        self.temperature = ATTACK_TEMP
        self.top_p = ATTACK_TOP_P

        self.category = category
        self.evaluate_locally = evaluate_locally
        self.model = load_indiv_model(model_name, 
                                      local = evaluate_locally, 
                                      use_jailbreakbench=False # Cannot use JBB as attacker
                                      )
        self.initialize_output = self.model.use_open_source_model
        self.template = FASTCHAT_TEMPLATE_NAMES[self.model_name]

    def preprocess_conversation(self, convs_list: list, prompts_list: list[str]):
        # For open source models, we can seed the generation with proper JSON
        init_message = ""
        if self.initialize_output:
            
            # Initalize the attack model's generated output to match format
            if len(convs_list[0].messages) == 0:# If is first message, don't need improvement
                init_message = '{"improvement": "","prompt": "'
            else:
                init_message = '{"improvement": "'
        for conv, prompt in zip(convs_list, prompts_list):
            if self.initialize_output:
                # 添加 system 提示（必须放前面）
                conv.append_message("system", "Please respond in JSON format with the keys 'improvement' and 'prompt'.")
            conv.append_message(conv.roles[0], prompt)
            if self.initialize_output:
                conv.append_message(conv.roles[1], init_message)
        openai_convs_list = [conv.to_openai_api_messages() for conv in convs_list]
        return openai_convs_list, init_message
        
    def _generate_attack(self, openai_conv_list: list[list[dict]], init_message: str):
        batchsize = len(openai_conv_list)
        indices_to_regenerate = list(range(batchsize))
        valid_outputs = [None] * batchsize
        new_adv_prompts = [None] * batchsize
        
        # Continuously generate outputs until all are valid or max_n_attack_attempts is reached
        for attempt in range(self.max_n_attack_attempts):
            # Subset conversations based on indices to regenerate
            convs_subset = [openai_conv_list[i] for i in indices_to_regenerate]
            # Generate outputs 
            outputs_list = self.model.batched_generate(convs_subset,
                                                        max_n_tokens = self.max_n_tokens,  
                                                        temperature = self.temperature,
                                                        top_p = self.top_p,
                                                        extra_eos_tokens=["}"]
                                                    )
            
            # Check for valid outputs and update the list
            new_indices_to_regenerate = []
            for i, full_output in enumerate(outputs_list):
                orig_index = indices_to_regenerate[i]
                full_output = init_message + full_output + "}" # Add end brace since we terminate generation on end braces
                attack_dict, json_str = extract_json(full_output)
                if attack_dict is not None:
                    valid_outputs[orig_index] = attack_dict
                    new_adv_prompts[orig_index] = json_str
                else:
                    new_indices_to_regenerate.append(orig_index)
            
            # Update indices to regenerate for the next iteration
            indices_to_regenerate = new_indices_to_regenerate
            # If all outputs are valid, break
            if not indices_to_regenerate:
                break

        if any([output is None for output in valid_outputs]):
            raise ValueError(f"Failed to generate valid output after {self.max_n_attack_attempts} attempts. Terminating.")
        return valid_outputs, new_adv_prompts

    def get_attack(self, convs_list, prompts_list):
        """
        Generates responses for a batch of conversations and prompts using a language model. 
        Only valid outputs in proper JSON format are returned. If an output isn't generated 
        successfully after max_n_attack_attempts, it's returned as None.
        
        Parameters:
        - convs_list: List of conversation objects.
        - prompts_list: List of prompts corresponding to each conversation.
        
        Returns:
        - List of generated outputs (dictionaries) or None for failed generations.
        """
        assert len(convs_list) == len(prompts_list), "Mismatch between number of conversations and prompts."
        
        # Convert conv_list to openai format and add the initial message
        processed_convs_list, init_message = self.preprocess_conversation(convs_list, prompts_list)
        valid_outputs, new_adv_prompts = self._generate_attack(processed_convs_list, init_message)

        for jailbreak_prompt, conv in zip(new_adv_prompts, convs_list):
            # For open source models, we can seed the generation with proper JSON and omit the post message
            # We add it back here
            if self.initialize_output:
                jailbreak_prompt += self.model.post_message
            conv.update_last_message(jailbreak_prompt)
        
        return valid_outputs

class TargetLM():
    """
        JailbreakBench class for target language models.
    """
    def __init__(self, 
            model_name: str, 
            category: str,
            max_n_tokens : int,
            phase: str,
            evaluate_locally: bool = False,
            use_jailbreakbench: bool = True,
            ):
        
        self.model_name = model_name
        self.max_n_tokens = max_n_tokens
        self.phase = phase
        self.use_jailbreakbench = use_jailbreakbench
        self.evaluate_locally = evaluate_locally

        from config import TARGET_TEMP,  TARGET_TOP_P   
        self.temperature = TARGET_TEMP
        self.top_p = TARGET_TOP_P

        self.model = load_indiv_model(model_name, evaluate_locally, use_jailbreakbench)            
        self.category = category

        self.template = FASTCHAT_TEMPLATE_NAMES[Model(model_name)]

    def get_response(self, prompts_list):
        if self.use_jailbreakbench:
            llm_response = self.model.query(prompts = prompts_list, 
                                behavior = self.category, 
                                phase = self.phase,
                                max_new_tokens=self.max_n_tokens)
            responses = llm_response.responses
        else:
            batchsize = len(prompts_list)
            convs_list = [conv_template(self.template) for _ in range(batchsize)]
            full_prompts = []
            for conv, prompt in zip(convs_list, prompts_list):
                conv.append_message(conv.roles[0], prompt)
                full_prompts.append(conv.to_openai_api_messages())

            responses = self.model.batched_generate(full_prompts, 
                                                            max_n_tokens = self.max_n_tokens,  
                                                            temperature = self.temperature,
                                                            top_p = self.top_p
                                                        )
           
        return responses