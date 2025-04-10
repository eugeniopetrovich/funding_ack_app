from flask import Flask, render_template, session, jsonify, request, send_file
import pandas as pd
import numpy as np
import io
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necessario per usare le sessioni

# Percorso relativo
base_dir = os.path.dirname(os.path.abspath(__file__))  # Ottieni la directory del file Python in esecuzione
CSV_file = os.path.join(base_dir, "acknowledgments.csv")

# CSV_file = "acknowledgments.csv"
# CSV_file = "ACk_Phil_Sci/my_flask_app/acknowledgments.csv"

# Dataframe di input
df = pd.read_csv(CSV_file, delimiter=",", encoding="UTF-8")

if "Funders" not in df.columns:
    df["Funders"] = ""  # Aggiunge la colonna vuota
    df.to_csv(CSV_file, index=False, encoding="UTF-8")
    
if "Funders_Text" not in df.columns:
    df["Funders_Text"] = ""  # Aggiunge la colonna vuota
    df.to_csv(CSV_file, index=False, encoding="UTF-8") 

if "row_id" not in df.columns:
    df["row_id"] = range(1, len(df) + 1)
    df["row_id"] = df["row_id"].astype(str)
    df.to_csv(CSV_file, index=False, encoding="UTF-8")


@app.route("/")
def index():
    
    # Se "current_index" non è in sessione, impostalo a 0
    if "current_index" not in session:
        session["current_index"] = 0
    
    current_index = session["current_index"]  # Recupera current_index dalla sessione
    
    ack_text = df.iloc[current_index]["Ack_text"]
    ut_id = df.iloc[current_index]["UT"]
    row_id = df.iloc[current_index]["row_id"]
    
    df_size = str(df.shape[0])
    
    
    return render_template("index.html",
                           ack_text=ack_text,
                           ut_id=ut_id,
                           row_id=row_id,
                           df_size=df_size)

@app.route("/initial_data", methods=["GET"])
def initial_data():
    try:
        
        global df  # Indica che stiamo modificando la variabile globale df
        df = pd.read_csv(CSV_file, delimiter=",", encoding="UTF-8")  # Ricarica il CSV in memoria
        
        current_index = session.get("current_index", 0)  # Usa il valore salvato in sessione
        # Leggi la prima riga del CSV
        first_row = df.iloc[current_index]  # Prendi la riga corrispondente al current index
        ack_text = first_row["Ack_text"]
        ut_id = first_row["UT"]
        funders_text = first_row.get("Funders_Text", "")  # Se manca, restituisce ""
        row_id = str(first_row.get("row_id", ""))
        df_size = str(df.shape[0])
        
        
        return jsonify({"ack_text": ack_text,
                        "ut_id": ut_id,
                        "funders_text": funders_text,
                        "row_id" : row_id,
                        "df_size" : df_size})
    
    except Exception as e:
        return jsonify({"message": f"Errore: {str(e)}"}), 500


@app.route("/next", methods=["POST"])
def next_ack():
    
    # Rileggo il csv
    df = pd.read_csv(CSV_file, dtype=str, encoding="UTF-8")  # dtype=str per evitare problemi con numeri
    
    # Recupera l'indice corrente dalla sessione
    current_index = session.get("current_index", 0)
    
    if current_index < len(df) - 1:  # Verifica che non siamo alla fine
        current_index += 1
    
    # Aggiorna l'indice nella sessione
    session["current_index"] = current_index 
    
    row = df.iloc[current_index]
    
    ack_text = row["Ack_text"]
    ut_id = row["UT"]
    funders_text = row.get("Funders_Text", "No funding organization found")
    row_id = row["row_id"]
    df_size = str(df.shape[0])
    
    if pd.isna(funders_text):  # Se è NaN, sostituiscilo con una stringa vuota
        funders_text = ""
    
    return jsonify({"ack_text": ack_text,
                    "ut_id": ut_id,
                    "funders_text": funders_text,
                    "row_id" : row_id,
                    "df_size" : df_size})



@app.route("/prev", methods=["POST"])
def prev_ack():
    
    # Rileggo il csv
    df = pd.read_csv(CSV_file, dtype=str, encoding="UTF-8")  # dtype=str per evitare problemi con numeri
    
    # Recupera l'indice corrente dalla sessione
    current_index = session.get("current_index", 0)
    
    if current_index > 0:  # Verifica che non siamo all'inizio
        current_index -= 1
        
    # Aggiorna l'indice nella sessione
    session["current_index"] = current_index 
    
        
    row = df.iloc[current_index]
    
    ack_text = row["Ack_text"]
    ut_id = row["UT"]
    funders_text = row.get("Funders_Text", "No funding organization found")
    row_id = row["row_id"]
    df_size = str(df.shape[0])
    
    if pd.isna(funders_text):  # Se è NaN, sostituiscilo con una stringa valida
        funders_text = ""
    
    return jsonify({"ack_text": ack_text,
                    "ut_id": ut_id,
                    "funders_text": funders_text,
                    "row_id" : row_id,
                    "df_size" : df_size})

@app.route("/save_selection", methods=["POST"])
def save_selection():
    # Ottieni i dati dal frontend
    data = request.json  
    selected_items = data.get("selected", []) # Selected ids
    formatted_text = data.get("formatted_text", "NaN") # Lista formattata
    ut_id = data.get("UT_id", "")
    

    if not ut_id:
        return jsonify({"message": "Dati mancanti!"}), 400
    
    try:
        # Carica il CSV in un DataFrame Pandas
        df = pd.read_csv(CSV_file, dtype=str, encoding="UTF-8")  # dtype=str per evitare problemi con numeri
        
        # Controlla se l'UT è presente nel CSV
        if ut_id not in df["UT"].values:
            return jsonify({"message": "UT non trovato nel CSV!"}), 404
        
        # Seleziona cosa scrivere nella colonna "Funders"
        if selected_items == "NaN" or not selected_items:  # Se vuoto o "NaN"
            funders_value = np.nan
        elif selected_items == "[No funding organization for this acknowledgment]":
            funders_value = "[No funding organization for this acknowledgment]"
        else:
            funders_value = ";".join(selected_items)
            
        if formatted_text == "NaN" or formatted_text.strip() == "":
            formatted_text = np.nan
        
        
        
        # Aggiorna la colonna 'Funders' per la riga corrispondente all'UT
        df.loc[df["UT"] == ut_id, "Funders"] = funders_value # Sovrascrive i finanziatori
        df.loc[df["UT"] == ut_id, "Funders_Text"] = formatted_text
        
        # Salva il file aggiornato
        df.to_csv(CSV_file, index=False, encoding="UTF-8")  # Mantiene la struttura originale

        return jsonify({"message": "Data saved successfully!"})

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route("/reset_funders", methods=["POST"])
def reset_funders():
    try:
        # Carica il CSV in un DataFrame Pandas
        df = pd.read_csv(CSV_file, dtype=str, encoding="UTF-8")
        df["Funders"] = np.nan
        df["Funders_Text"] = np.nan
        df.to_csv(CSV_file, index=False, encoding="UTF-8")
        return jsonify({"message": "Tutti gli inserimenti sono stati cancellati con successo."})
    except Exception as e:
        return jsonify({"message": f"Errore durante il reset: {str(e)}"}), 500


@app.route("/get_ack_text", methods=["GET"])
def get_ack_text():
    try:
        # Recupera l'ID UT dalla query string
        ut_id = request.args.get("ut_id")
        
        print(f"Ricevuto ut_id: {ut_id}") 
        
        # Rileggo il csv
        df = pd.read_csv(CSV_file, dtype=str, encoding="UTF-8")  # dtype=str per evitare problemi con numeri
        
        # Cerca la riga nel dataframe con l'UT corrispondente
        row = df[df["UT"] == ut_id]
        print(row.shape[0])
        # if not row.empty:
        if row.shape[0] > 0:
            # Se trovato, restituisci il testo di acknowledgment
            ack_text = row.iloc[0]["Ack_text"]
            ut_id = str(row.iloc[0]["UT"])
            funders_text = row.iloc[0]["Funders_Text"]
            row_id = str(row.iloc[0]["row_id"])
            df_size = str(df.shape[0])
            
            if pd.isna(funders_text):  # Se è NaN, sostituiscilo con una stringa valida
                funders_text = ""
            print(ack_text)
            print(type(ack_text))
            print(ut_id)
            print(type(ut_id))
            print(funders_text)
            print(type(funders_text))
            print(row_id)
            print(type(row_id))
            print(df_size)
            print(type(df_size))
            
            # Aggiorna l'indice corrente
            session["current_index"] = int(row.index[0])  # Imposta current_index con l'indice del dataframe
            
            return jsonify({
                "ack_text": ack_text,
                "ut_id": ut_id,
                "funders_text": funders_text,
                "row_id" : row_id,
                "df_size" : df_size
            })
        else:
            return jsonify({"message": "ID not found"}), 404
    except Exception as e:
        return jsonify({"message": f"Errore: {str(e)}"}), 500


@app.route("/export_csv", methods=["GET"])
def export_csv():
    # Rileggi il CSV
    df = pd.read_csv(CSV_file, dtype=str, encoding="UTF-8")
    
    # Seleziona solo le colonne rilevanti
    df = df[["UT", "Ack_text", "Funders"]]

    # Salva il CSV in memoria (non su disco)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="acknowledgments_funders_data.csv"
    )


if __name__ == '__main__':
    app.run(debug=True)
