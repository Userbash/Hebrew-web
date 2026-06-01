from .context_window import MODEL_WINDOWS
from .context_policy import should_compress
from .context_summarizer import summarize

class NativeContextManager:
    def build_context(self, task, memory_refs=None):
        refs = memory_refs or []
        text = "\n".join(refs)
        window = MODEL_WINDOWS.get("local-small", 8000)
        if should_compress(len(text)//4, window):
            text = summarize([text])
        return {"context": text, "window": window}
