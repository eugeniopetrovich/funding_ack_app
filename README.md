# Funding Bodies Search – Version 2

https://funding-ack-app.onrender.com

This is version 2 of the **Funding Bodies Search** web application. The app allows users to load acknowledgment texts from research papers and assign standardized funders using the [ROR (Research Organization Registry)](https://ror.org) API.

## 🚀 New Features in Version 2

- 🗃️ **File upload**: Upload your own `.csv` file.
- 🔍 **Autocomplete search**: Use the ROR API to search for funders by name.
- 💾 **Save funders**: Save one or more funders for each acknowledgment.
- 🚫 **Handle empty selections**: Mark an acknowledgment as having *no funding organization*.
- 🧭 **Navigation tools**:
  - **Next** / **Previous** to go through entries.
  - **Go to ID**: Jump directly to a record using its `UT` identifier.
- ✅ **Visual confirmation** after saving each entry.
- 📊 **Progress bar**: Tracks how many acknowledgments have already been annotated.
- 📦 **Export data**: Download your annotated dataset with a timestamped filename.
- 📝 **Instructions toggle**: Show/hide help instructions from the interface.

## 📄 File Format

Uploaded CSV files must contain at least the following columns:

- `UT` – unique identifier of the publication.
- `Ack_text` – the raw acknowledgment text.
- `AF` – the authors of the article.
- `PY` – the publication year of the article.
- `TI` – the title of the article.
- `JI`, `VL`, `IS`  – journal, volume, and issue of the article.
- `DI` – the DOI of the article.


Optional columns (`Funders`, `Funders_Text`, `row_id`) are automatically created if missing.

## License

MIT License
