import sys
import mistralai

# The latest mistralai SDK puts Mistral in mistralai.client
# but some libraries expect it in the root mistralai namespace.
try:
    from mistralai.client import Mistral
    mistralai.Mistral = Mistral
except ImportError:
    pass
