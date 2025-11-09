import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Optional, Tuple
from contextlib import contextmanager
import gc


class QwenReranker:
    def __init__(self, model_name: str = "Qwen/Qwen3-Reranker-0.6B", use_cuda: bool = True, 
                 use_flash_attention: bool = True, max_length: int = 32768):
        self.model_name = model_name
        self.use_cuda = use_cuda
        self.max_length = max_length
        
        self._initialize_model(use_flash_attention)
        self._setup_tokens()
        
    def _initialize_model(self, use_flash_attention: bool):
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, padding_side='left')
        
        model_kwargs = {"torch_dtype": torch.float16}
        if use_flash_attention:
            model_kwargs["attn_implementation"] = "flash_attention_2"
            
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, **model_kwargs)
        self.model = self.model.eval()
        
        # Start with model on CPU to save VRAM when not in use
        self.model_on_gpu = False
        if self.use_cuda and torch.cuda.is_available():
            # Only move to GPU during inference
            pass
        else:
            self.use_cuda = False
        
    def _setup_tokens(self):
        self.token_false_id = self.tokenizer.convert_tokens_to_ids("no")
        self.token_true_id = self.tokenizer.convert_tokens_to_ids("yes")
        
        prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        self.prefix_tokens = self.tokenizer.encode(prefix, add_special_tokens=False)
        self.suffix_tokens = self.tokenizer.encode(suffix, add_special_tokens=False)
    
    @contextmanager
    def gpu_context(self):
        """Context manager to handle GPU memory efficiently"""
        model_was_on_gpu = self.model_on_gpu
        
        try:
            # Move model to GPU if needed
            if self.use_cuda and not self.model_on_gpu:
                self.model = self.model.cuda()
                self.model_on_gpu = True
            yield
        finally:
            # Move model back to CPU if it wasn't there originally
            if self.use_cuda and not model_was_on_gpu and self.model_on_gpu:
                self.model = self.model.cpu()
                self.model_on_gpu = False
                torch.cuda.empty_cache()
                
    def clear_cache(self):
        """Explicitly clear GPU memory cache"""
        if self.use_cuda and torch.cuda.is_available():
            if self.model_on_gpu:
                self.model = self.model.cpu()
                self.model_on_gpu = False
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            gc.collect()
            
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.clear_cache()
        except:
            pass
        
    def format_instruction(self, instruction: Optional[str], query: str, doc: str) -> str:
        if instruction is None:
            instruction = 'Given a web search query, retrieve relevant passages that answer the query'
        return "<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}".format(
            instruction=instruction, query=query, doc=doc
        )
    
    def _process_inputs(self, pairs: List[str]) -> dict:
        inputs = self.tokenizer(
            pairs, padding=False, truncation='longest_first',
            return_attention_mask=False, 
            max_length=self.max_length - len(self.prefix_tokens) - len(self.suffix_tokens)
        )
        
        for i, ele in enumerate(inputs['input_ids']):
            inputs['input_ids'][i] = self.prefix_tokens + ele + self.suffix_tokens
            
        inputs = self.tokenizer.pad(inputs, padding=True, return_tensors="pt")
        
        for key in inputs:
            inputs[key] = inputs[key].to(self.model.device)
            
        return inputs
    
    @torch.no_grad()
    def _compute_logits(self, inputs: dict) -> List[float]:
        batch_scores = self.model(**inputs).logits[:, -1, :]
        true_vector = batch_scores[:, self.token_true_id]
        false_vector = batch_scores[:, self.token_false_id]
        batch_scores = torch.stack([false_vector, true_vector], dim=1)
        batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
        scores = batch_scores[:, 1].exp().tolist()
        return scores
    
    def rerank(self, query: str, documents: List[str],
               instruction: Optional[str] = None) -> List[float]:
        queries = [query for i in range(len(documents))]
            
        pairs = [self.format_instruction(instruction, query, doc) 
                for query, doc in zip(queries, documents)]
        
        with self.gpu_context():
            inputs = self._process_inputs(pairs)
            scores = self._compute_logits(inputs)
        
        return scores
    
    def rerank_query_documents(self, query: str, documents: List[str], 
                              instruction: Optional[str] = None) -> List[Tuple[str, float]]:
        scores = self.rerank(query, documents, instruction)
        
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        return doc_scores


if __name__ == "__main__":
    reranker = QwenReranker()
    
    task = 'Given a web search query, retrieve relevant passages that answer the query'
    
    query = "Explain gravity"
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
    ]
    
    scores = reranker.rerank(query, documents, task)
    print("scores: ", scores)
    
    # Clean up GPU memory after use
    reranker.clear_cache()
    print("GPU memory cleared")
