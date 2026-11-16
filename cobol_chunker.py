import re
import time
import requests

class CobolChunk:
    def __init__(self, global_data_context: str, procedure_code: str, chunk_index: int):
        self.global_data_context = global_data_context
        self.procedure_code = procedure_code
        self.chunk_index = chunk_index

class CobolChunker:
    def __init__(self, max_lines_per_chunk: int = 80):
        self.max_lines_per_chunk = max_lines_per_chunk

    def split(self, cobol_source: str) -> list[CobolChunk]:
        data_match = re.search(r'(IDENTIFICATION DIVISION\..*?)(PROCEDURE DIVISION\.)', cobol_source, re.DOTALL | re.IGNORECASE)
        if data_match:
            global_data_context = data_match.group(1).strip()
            procedure_block = cobol_source[data_match.end():].strip()
        else:
            global_data_context = "IDENTIFICATION DIVISION. PROGRAM-ID. UNKNOWN."
            procedure_block = cobol_source.strip()

        paragraphs = re.split(r'(\n\s*[0-9A-Z\-]+\.\s*\n)', procedure_block)
        chunks = []
        current_chunk = ""
        chunk_index = 1

        for para in paragraphs:
            if len(current_chunk.split('\n')) + len(para.split('\n')) > self.max_lines_per_chunk:
                if current_chunk.strip():
                    chunks.append(CobolChunk(global_data_context, current_chunk.strip(), chunk_index))
                    chunk_index += 1
                current_chunk = para
            else:
                current_chunk += para
                
        if current_chunk.strip():
            chunks.append(CobolChunk(global_data_context, current_chunk.strip(), chunk_index))
        return chunks

class ResilienceHarness:
    def __init__(self, executor_func, initial_window: int = 80, min_window: int = 20):
        self.executor_func = executor_func
        self.initial_window = initial_window
        self.min_window = min_window

    def process_file_with_resilience(self, cobol_source: str):
        window_sizes = [self.initial_window, 40, self.min_window]
        for window in window_sizes:
            try:
                print(f"[Harness] Tentando processar com janela de {window} linhas...")
                chunker = CobolChunker(max_lines_per_chunk=window)
                chunks = chunker.split(cobol_source)
                results = []
                for chunk in chunks:
                    result = self.executor_func(chunk)
                    results.append(result)
                return {"success": True, "window_size_used": window, "total_chunks": len(chunks), "results": results}
            except (requests.exceptions.HTTPError, requests.exceptions.Timeout) as e:
                print(f"[Harness] Falha com janela {window}: {e}. Reduzindo janela...")
                continue
        raise Exception("Falha fatal: Nao foi possivel processar o arquivo mesmo com a janela minima.")
