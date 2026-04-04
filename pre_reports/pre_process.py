import pandas as pd


def cleaned_pandas(file_path, columns_to_drop=None, index_col=None):
    """Load a CSV file into a DataFrame and remove pre-set columns.

    Args:
        file_path (str): Path to CSV file.
        columns_to_drop (list[str] | None): Columns to drop from dataframe.
        index_col (str | None): Column to set as DataFrame index.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    df = pd.read_csv(file_path)

    # Normalize paper names if present (trim + en-dash to hyphen)
    if "Paper Name:" in df.columns:
        df["Paper Name:"] = (
            df["Paper Name:"].astype(str).str.strip().str.replace('–', '-', regex=False)
        )

    if columns_to_drop:
        missing = [c for c in columns_to_drop if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found for dropping: {missing}")
        df = df.drop(columns=columns_to_drop)

    if index_col:
        if index_col not in df.columns:
            raise ValueError(f"Index column not found: {index_col}")
        df = df.set_index(index_col)

    return df




