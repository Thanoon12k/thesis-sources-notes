# Thesis Resource Manager

A modern desktop application to **organize, categorize, and manage** resources (paragraphs, references, media) for engineering theses with **IEEE & APA citation** support.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📝 **Paragraph Manager** | Write or paste text snippets linked to references |
| 📚 **IEEE & APA References** | Full citation formatting, parsing, and clipboard copy |
| 📂 **Multi-Thesis Support** | Switch between multiple theses / papers |
| 🏷️ **Color-Coded Categories** | Organize resources by topic |
| 📄 **PDF Attachment** | Attach reference PDFs and open them from the app |
| 🔗 **Reference URLs** | Store DOI / web links and open in browser |
| 🔍 **Search & Filter** | Quickly find resources and references |
| 🌙 **Dark / Light Mode** | Modern CustomTkinter UI with theme toggle |
| ⌨️ **Keyboard Shortcuts** | `Ctrl+S` to save |

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/Thanoon12k/thesis-sources-notes.git
cd thesis-sources-notes

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Usage

```bash
python app.py
```

The app opens as a compact centered window.

### Workflow

1. **Create a thesis** — click ＋ and give it a title (optionally attach the source PDF/DOCX)
2. **Paste paragraph** — write or paste a text snippet from the source
3. **Paste reference** — paste the IEEE or APA reference string (auto-parsed)
4. **Set page & category** — optional metadata
5. **Save** — the app auto-creates the reference, links it, and lists everything below

### Resource Card Actions

| Button | Description |
|---|---|
| ✏ Edit | Load resource back into the editor |
| 🗑 Delete | Remove the resource |
| 📋 Ref | Copy the formatted reference to clipboard |
| 🔗 Open | Open reference URL in browser |
| 📄 Open | Open attached PDF in system viewer |

---

## 🗂️ Project Structure

```
thesis-sources-notes/
├── app.py              # Main entry point
├── database.py         # SQLite schema + CRUD
├── citations.py        # IEEE & APA format / parse
├── file_handler.py     # PDF / DOCX file handling
├── panels/             # UI panel modules (legacy)
├── media/              # Attached PDFs (gitignored)
├── requirements.txt    # Python dependencies
├── .gitignore
└── README.md
```

## 🛠️ Tech Stack

- **GUI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (modern themed Tk)
- **Database**: SQLite (zero-config, portable single file)
- **PDF**: [PyMuPDF](https://pymupdf.readthedocs.io/) for rendering
- **DOCX**: [python-docx](https://python-docx.readthedocs.io/) for text extraction
- **Images**: [Pillow](https://pillow.readthedocs.io/)

## 📄 License

MIT
