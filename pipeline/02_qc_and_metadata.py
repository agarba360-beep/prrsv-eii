from Bio import SeqIO
import mysql.connector
from tqdm import tqdm
import numpy as np
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}
def run_qc():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute("SELECT accession, sequence FROM sequences_raw")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("⚠️ No sequences found for QC.")
        return

    print(f"🔍 Evaluating {len(rows)} sequences...")
    df = pd.DataFrame(rows, columns=["accession", "sequence"])
    df["length"] = df["sequence"].str.len()
    df["gc_content"] = df["sequence"].apply(lambda s: (s.count("G")+s.count("C"))/len(s))
    df["ambiguous"] = df["sequence"].str.count("N")
    df["quality_score"] = 1 - (df["ambiguous"]/df["length"])
    df["passed_qc"] = (df["length"].between(600, 700)) & (df["quality_score"] > 0.9)

        # --- Save QC results to DB ---
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qc_sequences (
            accession VARCHAR(50) PRIMARY KEY,
            sequence LONGTEXT,
            quality_score FLOAT,
            passed_qc BOOLEAN
        )
    """)
    conn.commit()

    passed = df[df["passed_qc"]]
    data = list(zip(
        passed["accession"],
        passed["sequence"],
        passed["quality_score"],
        passed["passed_qc"]
    ))

    cursor.executemany(
        "REPLACE INTO qc_sequences (accession, sequence, quality_score, passed_qc) VALUES (%s, %s, %s, %s)",
        data
    )

    conn.commit()
    conn.close()


    print(f"✅ QC complete. Passed: {len(passed)}/{len(df)} sequences.")

if __name__ == "__main__":
    run_qc()

