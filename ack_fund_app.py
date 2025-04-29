from flask import Flask, render_template, session, jsonify, request, send_file, redirect, url_for
import pandas as pd
import numpy as np
import io
import os
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY', 'dev-key')


# Cartella dove salveremo i file caricati
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Assicurati che la cartella di upload esista
if not os.path.exists(UPLOAD_FOLDER):
    print("Ciao. Cartella non esiste!")
    os.makedirs(UPLOAD_FOLDER)





@app.route("/")
def index():
    
    # Se "current_index" non è in sessione, impostalo a 0
    if "current_index" not in session:
        session["current_index"] = 0
        
    # Verifica se un file è stato caricato
    is_df = "filepath" in session and os.path.exists(session["filepath"])
    
    # Recupera eventuali messaggi dalla sessione e poi li cancella
    message = session.get("message", None)
    uploaded_filename = session.get("uploaded_filename", None)
    
    return render_template("index.html",
                           is_df=is_df,
                           message=message, 
                           uploaded_filename=uploaded_filename)



@app.route("/initial_data", methods=["GET"])
def initial_data():
    try:
        # Se l'utente ha già caricato un file, il suo path è in session["filepath"]
        if "filepath" in session and os.path.exists(session["filepath"]):
            
            filepath = session["filepath"]
            
            df = pd.read_csv(filepath)
        
            current_index = session.get("current_index", 0)  # Usa il valore salvato in sessione
            # Prendi la riga corrispondente al current index
            first_row = df.iloc[current_index]
            
            
            ack_text = first_row["Ack_text"].strip()
            if pd.isna(ack_text):
                ack_text = "0"
            
            ut_id = first_row["UT"]
            
            funders_text = first_row["Funders_Text"]
            if pd.isna(funders_text):
                funders_text = ""
                
            row_id = str(first_row["row_id"])
            
            df_size = str(df.shape[0])
            
            is_df = True
            
            # Metadata
            authors = str(first_row["AF"]).strip()
            title = str(first_row["TI"]).strip()
            pub_year = str(first_row["PY"]).strip()
            journal = str(first_row["JI"]).strip()
            vol = str(first_row["VL"]).strip()
            issue = str(first_row["IS"]).strip()
            doi = str(first_row["DI"]).strip()
            
            # Create the bibliographic reference from metadata
            bib_parts = []

            if authors:
                bib_parts.append(authors)
            if pub_year:
                bib_parts.append(f"({pub_year})")
            if title:
                bib_parts.append(f"'{title}'")
            if journal:
                bib_parts.append(f"<em>{journal}</em>")
            if vol:
                volume_part = vol
                if issue:
                    volume_part += f"({issue})"
                bib_parts.append(volume_part)
            if doi:
                doi_url = f"https://doi.org/{doi}"
                doi_link = f'<a href="{doi_url}" target="_blank" rel="noopener noreferrer">{doi_url}</a>'
                bib_parts.append(doi_link)

            # Unisci i pezzi con spazi
            bib_ref = " ".join(bib_parts)
            
            # Calcolo items già compilati
            n_empty_rows = df.index[df["Funders_Text"].isna() | (df["Funders_Text"] == "")].shape[0]
            completed_rows = str(df.shape[0] - n_empty_rows)
            

        else:
            # Se df non è caricato, restituisci valori di default
            ack_text = ""
            ut_id = "-"
            funders_text = ""
            row_id = "-"
            df_size = "-"
            is_df = False
            bib_ref = ""
            completed_rows = ""
        
        return jsonify({"ack_text": ack_text,
                        "ut_id": ut_id,
                        "funders_text": funders_text,
                        "row_id" : row_id,
                        "df_size" : df_size,
                        "is_df" : is_df,
                        "bib_ref": bib_ref,
                        "completed_rows": completed_rows})
    
    except Exception as e:
        return jsonify({"message": f"Errore: {str(e)}"}), 500

    
    
@app.route('/upload', methods=['POST'])
def upload_file():
    
    if 'file' not in request.files:
        session["message"] = "Errore: Nessun file selezionato."
        session["is_df"] = False
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        session["message"] = "Errore: Nessun file selezionato."
        session["is_df"] = False
        return redirect(request.url)

    if file and file.filename.endswith('.csv'):
        # Salva il file nella cartella uploads
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath) 
        
        try:         
            
            # Carica il file CSV in un dataframe
            df = pd.read_csv(filepath)
            
            # Controlla la presenza delle colonne obbligatorie
            required_columns = {"UT", "Ack_text", "AF", "PY", "TI", "JI", "VL", "IS", "DI"}
            
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                missing_cols = ", ".join(missing)
                session["message"] = f"Errore: colonne mancanti: {missing_cols}."
                session["is_df"] = False
                
                return redirect(url_for('index'))
            

            # Aggiunge colonne opzionali se mancanti
            if "Funders" not in df.columns:
                df["Funders"] = ""  # Aggiunge la colonna vuota  
                
            if "Funders_Text" not in df.columns:
                df["Funders_Text"] = ""  # Aggiunge la colonna vuota
            
            if "row_id" not in df.columns:
                df["row_id"] = range(1, len(df) + 1)
                df["row_id"] = df["row_id"].astype(str)
                
            # Imposta current_index: prima riga con Funders_Text vuoto
            empty_rows = df.index[df["Funders_Text"].isna() | (df["Funders_Text"] == "")].tolist()
            session["current_index"] = empty_rows[0] if empty_rows else 0
            
            # Salva su disco e in sessione
            df.to_csv(filepath, index=False, encoding="UTF-8")
            session['uploaded_filename'] = filename
            session['filepath'] = filepath
            session["is_df"] = True
            session["message"] = "File uploaded successfully!"
            
            return redirect(url_for('index'))

        except Exception as e:
            session["message"] = f"Errore nel caricamento del file: {str(e)}"
            session["is_df"] = False
            return redirect(url_for('index'))
    else:
        session["message"] = "Errore: formato non supportato. Carica un file .csv"
        session["is_df"] = False
        return redirect(url_for('index'))




@app.route("/next", methods=["POST"])
def next_ack():
    
    if "filepath" in session and os.path.exists(session["filepath"]):
        filepath = session["filepath"]
        df = pd.read_csv(filepath)
    
        # Recupera l'indice corrente dalla sessione
        current_index = session.get("current_index", 0)
    
        if current_index < len(df) - 1:  # Verifica che non siamo alla fine
            current_index += 1
            # Aggiorna l'indice nella sessione
            session["current_index"] = current_index 
        
        row = df.iloc[current_index]
    
        ack_text = str(row["Ack_text"]).strip()
        ut_id = str(row["UT"])
        
        funders_text = row.get("Funders_Text", "")
        if pd.isna(funders_text):  # Se è NaN, sostituiscilo con una stringa vuota
            funders_text = ""
            
        row_id = str(row["row_id"])
        df_size = str(df.shape[0])
        
        # Calcolo items già compilati
        n_empty_rows = df.index[df["Funders_Text"].isna() | (df["Funders_Text"] == "")].shape[0]
        completed_rows = str(df.shape[0] - n_empty_rows)
        
        
        # Metadata
        authors = str(row["AF"]).strip()
        title = str(row["TI"]).strip()
        pub_year = str(row["PY"]).strip()
        journal = str(row["JI"]).strip()
        vol = str(row["VL"]).strip()
        issue = str(row["IS"]).strip()
        doi = str(row["DI"]).strip()
        
        # Create the bibliographic reference from metadata
        bib_parts = []

        if authors:
            bib_parts.append(authors)
        if pub_year:
            bib_parts.append(f"({pub_year})")
        if title:
            bib_parts.append(f"'{title}'")
        if journal:
            bib_parts.append(f"<em>{journal}</em>")
        if vol:
            volume_part = vol
            if issue:
                volume_part += f"({issue})"
            bib_parts.append(volume_part)
        if doi:
            doi_url = f"https://doi.org/{doi}"
            doi_link = f'<a href="{doi_url}" target="_blank" rel="noopener noreferrer">{doi_url}</a>'
            bib_parts.append(doi_link)

        # Unisci i pezzi con spazi
        bib_ref = " ".join(bib_parts)
    
        
        return jsonify({"ack_text": ack_text,
                    "ut_id": ut_id,
                    "funders_text": funders_text,
                    "row_id" : row_id,
                    "df_size" : df_size,
                    "is_df": True,
                    "bib_ref": bib_ref,
                    "completed_rows": completed_rows
                    })
    else:
        return jsonify({"message": "Nessun file caricato!", "is_df": False}), 400


@app.route("/prev", methods=["POST"])
def prev_ack():
    
    if "filepath" in session and os.path.exists(session["filepath"]):
        filepath = session["filepath"]
        df = pd.read_csv(filepath)
    
        # Recupera l'indice corrente dalla sessione
        current_index = session.get("current_index", 0)
    
        if current_index > 0:  # Verifica che non siamo all'inizio
            current_index -= 1
            # Aggiorna l'indice nella sessione
            session["current_index"] = current_index 
        
        row = df.iloc[current_index]
    
        ack_text = str(row["Ack_text"]).strip()
        ut_id = str(row["UT"])
        
        funders_text = row.get("Funders_Text", "")
        if pd.isna(funders_text):  # Se è NaN, sostituiscilo con una stringa valida
            funders_text = ""
            
        row_id = str(row["row_id"])
        df_size = str(df.shape[0])
        
        # Calcolo items già compilati
        n_empty_rows = df.index[df["Funders_Text"].isna() | (df["Funders_Text"] == "")].shape[0]
        completed_rows = str(df.shape[0] - n_empty_rows)
        
        
        # Metadata
        authors = str(row["AF"]).strip()
        title = str(row["TI"]).strip()
        pub_year = str(row["PY"]).strip()
        journal = str(row["JI"]).strip()
        vol = str(row["VL"]).strip()
        issue = str(row["IS"]).strip()
        doi = str(row["DI"]).strip()
        
        # Create the bibliographic reference from metadata
        bib_parts = []

        if authors:
            bib_parts.append(authors)
        if pub_year:
            bib_parts.append(f"({pub_year})")
        if title:
            bib_parts.append(f"'{title}'")
        if journal:
            bib_parts.append(f"<em>{journal}</em>")
        if vol:
            volume_part = vol
            if issue:
                volume_part += f"({issue})"
            bib_parts.append(volume_part)
        if doi:
            doi_url = f"https://doi.org/{doi}"
            doi_link = f'<a href="{doi_url}" target="_blank" rel="noopener noreferrer">{doi_url}</a>'
            bib_parts.append(doi_link)

        # Unisci i pezzi con spazi
        bib_ref = " ".join(bib_parts)
    
    
        return jsonify({"ack_text": ack_text,
                    "ut_id": ut_id,
                    "funders_text": funders_text,
                    "row_id" : row_id,
                    "df_size" : df_size,
                    "is_df": True,
                    "bib_ref": bib_ref,
                    "completed_rows": completed_rows
                    })
    else:
        return jsonify({"message": "Nessun file caricato!", "is_df": False}), 400
        
@app.route("/save_selection", methods=["POST"])
def save_selection():
    
    if "filepath" not in session or not os.path.exists(session["filepath"]):
        return jsonify({"message": "Nessun file caricato!"}), 400
    
    try:
        filepath = session["filepath"]
        df = pd.read_csv(filepath)

        # Ottieni i dati dal frontend
        data = request.json  
        selected_items = data.get("selected", []) # Selected ids
        formatted_text = data.get("formatted_text", "NaN") # Lista formattata
        ut_id = data.get("UT_id", "")
    
        if not ut_id:
            return jsonify({"message": "Dati mancanti!"}), 400
        
        if ut_id not in df["UT"].values:
            return jsonify({"message": "UT non trovato nel CSV!"}), 404
    
        # Imposta valori da salvare
        if not selected_items or selected_items == "NaN":
            funders_value = np.nan
        elif selected_items == ["[No funding organization for this acknowledgment]"]:
            funders_value = ["[No funding organization for this acknowledgment]"]
        else:
            funders_value = ";".join(selected_items)
            
        if formatted_text == "NaN" or formatted_text.strip() == "":
                formatted_text = np.nan
        
        # Aggiorna la colonna 'Funders' per la riga corrispondente all'UT
        df.loc[df["UT"] == ut_id, "Funders"] = funders_value # Sovrascrive i finanziatori
        df.loc[df["UT"] == ut_id, "Funders_Text"] = formatted_text

        # Sovrascrive il CSV
        df.to_csv(filepath, index=False)

        return jsonify({"message": "Dati salvati correttamente!"})         

    except Exception as e:
        return jsonify({"message": f"Errore: {str(e)}"}), 500
    
        

@app.route("/get_ack_text", methods=["GET"])
def get_ack_text():
    
    if "filepath" not in session or not os.path.exists(session["filepath"]):
        return jsonify({"message": "Nessun file caricato!"}), 400

    try:
        filepath = session["filepath"]
        df = pd.read_csv(filepath)
        
        # Recupera l'ID UT dalla query string
        ut_id = request.args.get("ut_id")
    
        # Cerca la riga nel dataframe con l'UT corrispondente
        row = df[df["UT"] == ut_id]
    
        # if not row.empty:
        if row.shape[0] > 0:
            # Se trovato, restituisci il testo di acknowledgment
            ack_text = row.iloc[0]["Ack_text"].strip()
            ut_id = str(row.iloc[0]["UT"])
            funders_text = row.iloc[0]["Funders_Text"]
            row_id = str(row.iloc[0]["row_id"])
            df_size = str(df.shape[0])
            
            # Calcolo items già compilati
            n_empty_rows = df.index[df["Funders_Text"].isna() | (df["Funders_Text"] == "")].shape[0]
            completed_rows = str(df.shape[0] - n_empty_rows)
            
            
            # Metadata
            authors = str(row.iloc[0]["AF"]).strip()
            title = str(row.iloc[0]["TI"]).strip()
            pub_year = str(row.iloc[0]["PY"]).strip()
            journal = str(row.iloc[0]["JI"]).strip()
            vol = str(row.iloc[0]["VL"]).strip()
            issue = str(row.iloc[0]["IS"]).strip()
            doi = str(row.iloc[0]["DI"]).strip()
            
            # Create the bibliographic reference from metadata
            bib_parts = []

            if authors:
                bib_parts.append(authors)
            if pub_year:
                bib_parts.append(f"({pub_year})")
            if title:
                bib_parts.append(f"'{title}'")
            if journal:
                bib_parts.append(f"<em>{journal}</em>")
            if vol:
                volume_part = vol
                if issue:
                    volume_part += f"({issue})"
                bib_parts.append(volume_part)
            if doi:
                doi_url = f"https://doi.org/{doi}"
                doi_link = f'<a href="{doi_url}" target="_blank" rel="noopener noreferrer">{doi_url}</a>'
                bib_parts.append(doi_link)

            # Unisci i pezzi con spazi
            bib_ref = " ".join(bib_parts)
            
        
            if pd.isna(funders_text):  # Se è NaN, sostituiscilo con una stringa valida
                funders_text = ""
        
            # Aggiorna l'indice corrente
            session["current_index"] = int(row.index[0])  # Imposta current_index con l'indice del dataframe
        
            return jsonify({
                "ack_text": ack_text,
                "ut_id": ut_id,
                "funders_text": funders_text,
                "row_id" : row_id,
                "df_size" : df_size,
                "is_df": True,
                "bib_ref": bib_ref,
                "completed_rows": completed_rows                
            })
        else:
            return jsonify({"message": "ID not found"}), 404
    except Exception as e:
        return jsonify({"message": f"Errore: {str(e)}"}), 500
    


@app.route("/export_csv", methods=["GET"])
def export_csv():
    
    if "filepath" in session and os.path.exists(session["filepath"]):
        
        filepath = session["filepath"]
        
        try:
            df = pd.read_csv(filepath)
    
            # Seleziona solo le colonne rilevanti
            df = df[["UT", "Ack_text", "AF", "PY", "TI", "JI", "VL", "IS", "DI", "Funders", "Funders_Text"]]

            # Salva il CSV in memoria (non su disco)
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)

             # Genera il timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ack_funders_data_{timestamp}.csv"
            
            return send_file(
                io.BytesIO(output.getvalue().encode("utf-8")),
                mimetype="text/csv",
                as_attachment=True,
                download_name=filename
            )
        
        except Exception as e:
            return jsonify({"message": f"Errore durante l'esportazione: {str(e)}"}), 500
    else:
        return jsonify({"message": "Nessun file caricato!"}), 400


if __name__ == '__main__':
    app.run(debug=True)
