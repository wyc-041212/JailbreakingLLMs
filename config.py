from enum import Enum
VICUNA_PATH = "/home/comp/f2256768/JBShield/models/vicuna-13b-v1.5"
LLAMA_PATH = "/home/pchao/Llama-2-7b-chat-hf"
QWEN_PATH = "/home/comp/f2256768/JBShield/models/Qwen2.5-7B-Instruct"
DEEPSEEK_PATH = "/home/comp/f2256768/JBShield/models/DeepSeek-R1-Distill-Qwen-7B"

ATTACK_TEMP = 1
TARGET_TEMP = 0.7
ATTACK_TOP_P = 0.9
TARGET_TOP_P = 1


## MODEL PARAMETERS ##
class Model(Enum):
    vicuna = "vicuna-13b-v1.5"
    llama_2 = "llama-2-7b-chat-hf"
    gpt_3_5 = "gpt-3.5-turbo-1106"
    gpt_4 = "gpt-4-0125-preview"
    claude_1 = "claude-instant-1.2"
    claude_2 = "claude-2.1"
    gemini = "gemini-pro"
    mixtral = "mixtral"
    qwen = "qwen-2.5-7b-instruct"
    deepseek = "deepseek-r1-distill-qwen-7b"

MODEL_NAMES = [model.value for model in Model]

HF_MODEL_NAMES: dict[Model, str] = {
    Model.llama_2: "meta-llama/Llama-2-7b-chat-hf",
    # Model.vicuna: "lmsys/vicuna-13b-v1.5",
    Model.vicuna: "/home/comp/f2256768/JBShield/models/vicuna-13b-v1.5",
    Model.mixtral: "mistralai/Mixtral-8x7B-Instruct-v0.1",
    # Model.qwen: "Qwen/Qwen2.5-7B-Instruct",
    Model.qwen: "/home/comp/f2256768/JBShield/models/Qwen2.5-7B-Instruct",
    # Model.deepseek: "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    Model.deepseek: "/home/comp/f2256768/JBShield/models/DeepSeek-R1-Distill-Qwen-7B"
}

TOGETHER_MODEL_NAMES: dict[Model, str] = {
    Model.llama_2: "together_ai/togethercomputer/llama-2-7b-chat",
    Model.vicuna: "together_ai/lmsys/vicuna-13b-v1.5",
    Model.mixtral: "together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1"
}

FASTCHAT_TEMPLATE_NAMES: dict[Model, str] = {
    Model.gpt_3_5: "gpt-3.5-turbo",
    Model.gpt_4: "gpt-4",
    Model.claude_1: "claude-instant-1.2",
    Model.claude_2: "claude-2.1",
    Model.gemini: "gemini-pro",
    Model.vicuna: "vicuna_v1.1",
    Model.llama_2: "llama-2-7b-chat-hf",
    Model.mixtral: "mixtral",
    Model.qwen: "qwen-7b-chat",
    Model.deepseek: "qwen-7b-chat",
}

API_KEY_NAMES: dict[Model, str] = {
    Model.gpt_3_5:  "OPENAI_API_KEY",
    Model.gpt_4:    "OPENAI_API_KEY",
    Model.claude_1: "ANTHROPIC_API_KEY",
    Model.claude_2: "ANTHROPIC_API_KEY",
    Model.gemini:   "GEMINI_API_KEY",
    Model.vicuna:   "TOGETHER_API_KEY",
    Model.llama_2:  "TOGETHER_API_KEY",
    Model.mixtral:  "TOGETHER_API_KEY",
    Model.qwen: None,
    Model.deepseek: None,
}

LITELLM_TEMPLATES: dict[Model, dict] = {
    Model.vicuna: {"roles":{
                    "system": {"pre_message": "", "post_message": " "},
                    "user": {"pre_message": "USER: ", "post_message": " ASSISTANT:"},
                    "assistant": {"pre_message": "", "post_message": "", },
                },
                "post_message":"</s>",
                "initial_prompt_value" : "",
                "eos_tokens": ["</s>"]         
                },
    Model.llama_2: {"roles":{
                    "system": {"pre_message": "[INST] <<SYS>>\n", "post_message": "\n<</SYS>>\n\n"},
                    "user": {"pre_message": "", "post_message": " [/INST]"},
                    "assistant": {"pre_message": "", "post_message": ""},
                },
                "post_message" : " </s><s>",
                "initial_prompt_value" : "",
                "eos_tokens" :  ["</s>", "[/INST]"]  
            },
    Model.mixtral: {"roles":{
                    "system": {"pre_message": "[INST] ", "post_message": " [/INST]"},
                    "user": {"pre_message": "[INST] ", "post_message": " [/INST]"},
                    "assistant": {"pre_message": " ", "post_message": "",}
                },
                "post_message": "</s>",
                "initial_prompt_value" : "<s>",
                "eos_tokens": ["</s>", "[/INST]"]
    },
    Model.qwen: {"roles":{
                    "system": {"pre_message": "<|im_start|>system\n", "post_message": "<|im_end|>"},
                    "user": {"pre_message": "\n<|im_start|>user\n", "post_message": "<|im_end|>"},
                    "assistant": {"pre_message": "\n<|im_start|>assistant\n", "post_message": "<|im_end|>"}
                },
                "post_message": "",
                "initial_prompt_value": "",
                "eos_tokens": ["<|im_end|>"]
    },
    Model.deepseek: {"roles":{
                    "system": {"pre_message": "<|im_start|>system\n", "post_message": "<|im_end|>"},
                    "user": {"pre_message": "\n<|im_start|>user\n", "post_message": "<|im_end|>"},
                    "assistant": {"pre_message": "\n<|im_start|>assistant\n", "post_message": "<|im_end|>"}
                },
                "post_message": "",
                "initial_prompt_value": "",
                "eos_tokens": ["<|im_end|>"]
    },

    # Model.qwen: {"roles": {"system": {"pre_message": "", "post_message": ""},
    #         "user": {"pre_message": "<|user|>\n", "post_message": "<|assistant|>\n"},
    #         "assistant": {"pre_message": "", "post_message": ""}
    #     },
    #     "post_message": "<|endoftext|>",
    #     "initial_prompt_value": "",
    #     "eos_tokens": ["<|endoftext|>"]
    # },
    # Model.deepseek: {
    #     "roles": {
    #         "system": {"pre_message": "", "post_message": ""},
    #         "user": {"pre_message": "<|user|>\n", "post_message": "<|assistant|>\n"},
    #         "assistant": {"pre_message": "", "post_message": ""}
    #     },
    #     "post_message": "<|endoftext|>",
    #     "initial_prompt_value": "",
    #     "eos_tokens": ["<|endoftext|>"]
    # }
}