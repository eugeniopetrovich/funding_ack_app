# Funding Bodies Search – Version 2

https://funding-ack-app.onrender.com

This is version 2 of the **Funding Bodies Search** web application. The app allows users to load acknowledgment texts from research papers and assign standardized funders using the [ROR (Research Organization Registry)](https://ror.org) API.

## 🚀 New Features in Version 2

- 🗃️ **File upload**: Upload your own `.csv` file with columns `UT` and `Ack_text`.
- 🔍 **Autocomplete search**: Use the ROR API to search for funders by name or affiliation.
- 💾 **Save funders**: Save one or more funders for each acknowledgment line.
- 🧭 **Navigation tools**:
  - **Next** / **Previous** to go through entries.
  - **Go to ID**: Jump directly to a record using its `UT` identifier.
- ✅ **Visual confirmation** after saving each entry.
- 📦 **Export data**: Download your annotated dataset with a timestamped filename.
- 📝 **Instructions toggle**: Show/hide help instructions from the interface.

## 📄 File Format

Uploaded CSV files must contain at least the following columns:

- `UT` – unique identifier of the publication.
- `Ack_text` – the raw acknowledgment text.

Optional columns (`Funders`, `Funders_Text`, `row_id`) are automatically created if missing.

## License

MIT License
