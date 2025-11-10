import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Optional


class QwenReranker:
    """
    A class to encapsulate the Qwen Reranker model for easy reuse.

    This class handles model and tokenizer loading, input formatting,
    and scoring of query-document pairs.
    """

    def __init__(self,
                 model_name_or_path: str = "Qwen/Qwen3-Reranker-0.6B",
                 torch_dtype: torch.dtype = torch.bfloat16,
                 use_flash_attention_2: bool = False,
                 device: Optional[str] = None,
                 max_length: int = 8192):
        """
        Initializes the QwenReranker.

        Args:
            model_name_or_path (str): The name or path of the reranker model.
            torch_dtype (torch.dtype): The data type for model weights (e.g., torch.bfloat16).
            use_flash_attention_2 (bool): Whether to use flash_attention_2 for acceleration.
            device (Optional[str]): The device to run the model on ('cuda', 'cpu', etc.).
                                    Auto-detects if None.
            max_length (int): The maximum sequence length for the model.
        """
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device}")

        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, padding_side='left')

        model_args = {'torch_dtype': torch_dtype}
        if use_flash_attention_2:
            if torch.cuda.is_available():
                model_args['attn_implementation'] = "flash_attention_2"
                print("Using flash_attention_2.")
            else:
                print("Warning: flash_attention_2 is requested but CUDA is not available. Falling back to default.")

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path, **model_args
        ).to(self.device).eval()

        self.token_false_id = self.tokenizer.convert_tokens_to_ids("no")
        self.token_true_id = self.tokenizer.convert_tokens_to_ids("yes")

        # Pre-tokenize the instruction templates
        prefix_text = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        suffix_text = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        self.prefix_tokens = self.tokenizer.encode(prefix_text, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(suffix_text, add_special_tokens=False)

    def _format_instruction(self, query: str, doc: str, instruction: Optional[str] = None) -> str:
        """Formats the input string for the model."""
        if instruction is None:
            instruction = 'Given a web search query, retrieve relevant passages that answer the query'
        return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"

    def _prepare_inputs(self, formatted_pairs: List[str]) -> dict:
        """Tokenizes, adds special tokens, pads, and moves inputs to the correct device."""
        inputs = self.tokenizer(
            formatted_pairs,
            padding=False,
            truncation='longest_first',
            return_attention_mask=False,
            max_length=self.max_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        )
        # Manually add prefix and suffix tokens
        for i in range(len(inputs['input_ids'])):
            inputs['input_ids'][i] = self.prefix_tokens + inputs['input_ids'][i] + self.suffix_tokens

        # Pad the batch
        inputs = self.tokenizer.pad(inputs, padding=True, return_tensors="pt", max_length=self.max_length)

        # Move to device
        for key in inputs:
            inputs[key] = inputs[key].to(self.device)
        return inputs

    @torch.no_grad()
    def compute_scores(self, query: str, documents: List[str], instruction: Optional[str] = None,
                       batch_size: int = 4) -> List[float]:
        """
        Computes relevance scores for a list of documents given a single query.

        Args:
            query (str): The search query.
            documents (List[str]): A list of documents to be ranked.
            instruction (Optional[str]): A custom instruction for the task. If None, a default is used.
            batch_size (int): The number of documents to process in a single batch.

        Returns:
            List[float]: A list of relevance scores, one for each document.
        """
        all_scores = []
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            formatted_pairs = [self._format_instruction(query, doc, instruction) for doc in batch_docs]

            inputs = self._prepare_inputs(formatted_pairs)

            logits = self.model(**inputs).logits[:, -1, :]

            # Extract scores for "yes" and "no" tokens
            true_scores = logits[:, self.token_true_id]
            false_scores = logits[:, self.token_false_id]

            # Combine and apply softmax
            batch_scores = torch.stack([false_scores, true_scores], dim=1)
            batch_log_softmax = torch.nn.functional.log_softmax(batch_scores, dim=1)

            # Get the probability of "yes"
            scores = batch_log_softmax[:, 1].exp().tolist()
            all_scores.extend(scores)

        return all_scores


# --- Example Usage ---
if __name__ == "__main__":
    # 1. Initialize the reranker
    # Set use_flash_attention_2=True if you have flash-attn installed and a supported GPU
    try:
        reranker = QwenReranker(use_flash_attention_2=True)
    except ImportError:
        print("flash-attn not installed. Falling back to default attention.")
        reranker = QwenReranker(use_flash_attention_2=False)

    # 2. Define your query and documents
    query = "Explain the theory of relativity"
    documents = [
        "The theory of relativity, developed by Albert Einstein, is a cornerstone of modern physics. It is divided into two parts: special relativity and general relativity.",
        "The capital of France is Paris, a major European city and a global center for art, fashion, gastronomy, and culture.",
        "General relativity is a theory of gravitation that describes gravity not as a force, but as a consequence of the curvature of spacetime caused by the mass and energy of objects.",
        "Special relativity deals with the relationship between space and time for objects moving at constant speeds in a straight line. It introduced the famous equation E=mc².",
        "Quantum mechanics is a fundamental theory in physics that provides a description of the physical properties of nature at the scale of atoms and subatomic particles."
    ]

    # 3. Compute scores
    scores = reranker.compute_scores(query, documents)

    # 4. Print ranked results
    print(f"Query: {query}\n")
    print("Ranked Documents:")

    # Combine documents and scores, then sort
    ranked_results = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)

    for i, (doc, score) in enumerate(ranked_results):
        print(f"Rank {i + 1} (Score: {score:.4f}): {doc}")