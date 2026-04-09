import os
import mysql.connector
import numpy as np
from Bio import SeqIO
import re
from scipy.spatial.distance import pdist

# ---------- DATABASE CONFIG ----------
from dotenv import load_dotenv
import os

load_dotenv()

config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}
# ---------- LOAD SEQUENCES ----------
aligned_file = "data/alignments/orf5_codon_aligned.fasta"

records = list(SeqIO.parse(aligned_file, "fasta"))
print(f"✅ Loaded {len(records)} codon-aligned sequences.")

if len(records) == 0:
    raise Exception("No sequences found in alignment file.")

# Keep alignment gaps
seqs = [str(r.seq).upper() for r in records]

# Ensure equal lengths
max_len = max(len(s) for s in seqs)
seqs = [s.ljust(max_len, "-") for s in seqs]

# Alignment matrix
arr = np.array([list(s) for s in seqs])

# ---------- NORMALIZATION ----------
def normalize(values):
    vals = np.array(values, dtype=float)

    if len(vals) == 0:
        return 0.0

    if np.max(vals) == 0:
        return 0.0

    vals = vals - np.min(vals)

    return float(np.mean(vals / (np.max(vals) + 1e-9)))


# ---------- 1️⃣ Epitope Drift (Shannon Entropy) ----------
entropy_vals = []

for col in arr.T:
    bases, counts = np.unique(col, return_counts=True)
    freqs = counts / np.sum(counts)
    entropy = -np.sum(freqs * np.log2(freqs))
    entropy_vals.append(entropy)

epitope_norm = normalize(entropy_vals)


# ---------- 2️⃣ Selection Pressure (Codon Variability) ----------
codon_variability = []

for col in range(0, arr.shape[1] - 2, 3):
    codons = []

    for row in arr:
        codon = "".join(row[col : col + 3])

        if "-" not in codon:
            codons.append(codon)

    codon_variability.append(len(set(codons)))

selection_norm = normalize(codon_variability)


# ---------- 3️⃣ Glycosylation Dynamics ----------
glyco_counts = []

for seq in seqs:
    motifs = re.findall(r"N[^P][ST]", seq)
    glyco_counts.append(len(motifs))

glyco_norm = normalize(glyco_counts)


# ---------- 4️⃣ Phylogenetic Instability ----------

# Convert nucleotides to numeric encoding so SciPy can compute distances
mapping = {
    "A": 0,
    "T": 1,
    "G": 2,
    "C": 3,
    "-": 4,
    "N": 5,
}

numeric_arr = np.vectorize(lambda x: mapping.get(x, 5))(arr)

phylo_dist = pdist(numeric_arr, metric="hamming")

phylo_norm = normalize(phylo_dist)


# ---------- 5️⃣ Distance Outliers ----------
mean_dist = np.mean(phylo_dist)
std_dist = np.std(phylo_dist)

outliers = phylo_dist > (mean_dist + 2 * std_dist)

outlier_norm = float(np.mean(outliers))


# ---------- SIGNALS ----------
signals = {
    "EpitopeDrift": epitope_norm,
    "SelectionPressure": selection_norm,
    "GlycosylationDynamics": glyco_norm,
    "PhylogeneticInstability": phylo_norm,
    "DistanceOutliers": outlier_norm,
}


# ---------- WEIGHTED EII ----------
weights = {
    "EpitopeDrift": 0.30,
    "SelectionPressure": 0.25,
    "GlycosylationDynamics": 0.20,
    "PhylogeneticInstability": 0.15,
    "DistanceOutliers": 0.10,
}

EII = sum(signals[k] * weights[k] for k in signals) * 100

print("\n🧬 EII Computed:", round(EII, 2))

for k, v in signals.items():
    print(f"{k}: {v:.3f}")


# ---------- STORE IN DATABASE ----------
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Insert into history
cursor.execute(
    "INSERT INTO eii_index (eii_value) VALUES (%s)",
    (EII,),
)

# Update signals
cursor.execute("DELETE FROM eii_signals")

cursor.executemany(
    "INSERT INTO eii_signals (signal_name, mean_value) VALUES (%s,%s)",
    [(k, v) for k, v in signals.items()],
)

# Update latest snapshot
cursor.execute("SELECT COUNT(*) FROM eii_latest")
exists = cursor.fetchone()[0]

if exists == 0:

    cursor.execute(
        """
        INSERT INTO eii_latest (
        eii_value,
        epitope_drift,
        selection_pressure,
        glycosylation_dynamics,
        phylogenetic_instability,
        distance_outliers
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            EII,
            signals["EpitopeDrift"],
            signals["SelectionPressure"],
            signals["GlycosylationDynamics"],
            signals["PhylogeneticInstability"],
            signals["DistanceOutliers"],
        ),
    )

else:

    cursor.execute(
        """
        UPDATE eii_latest SET
        eii_value=%s,
        epitope_drift=%s,
        selection_pressure=%s,
        glycosylation_dynamics=%s,
        phylogenetic_instability=%s,
        distance_outliers=%s,
        last_updated=NOW()
        """,
        (
            EII,
            signals["EpitopeDrift"],
            signals["SelectionPressure"],
            signals["GlycosylationDynamics"],
            signals["PhylogeneticInstability"],
            signals["DistanceOutliers"],
        ),
    )

conn.commit()
conn.close()

print("✅ Database updated successfully.")
