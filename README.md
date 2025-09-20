# Python-Based Command Terminal

A simple Python-powered terminal that supports standard file operations, directory navigation, and process checks.  
It also includes NLP-powered commands for natural interactions.

---

## Features
- File and directory commands (`ls`, `cd`, `pwd`, `mkdir`, `rm`)
- NLP to terminal mapping (e.g., `create folder sample` → `mkdir sample`)
- Error handling for invalid commands
- Clean and responsive interface
- Hugging Face Space demo
- Tab Autocomplete Support

---

## Demo Instructions

Try commands like:

- `pwd`  
- `ls`  
- `mkdir demo`  
- `cd demo`  
- `status`  
- `create folder sample` → *(NLP → `mkdir sample`)*  
- `move folder sample to ..`  

---

## Live Demo 🚀

👉 [Click here to try it on Hugging Face](https://huggingface.co/spaces/Keshavpareek09/Keshav)  

*(Make sure your internet is stable. The Space will keep running even if you close your laptop/browser, as it is hosted on Hugging Face servers, not your local machine.)*

---

## Run Locally

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
python main.py
