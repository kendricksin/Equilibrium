import streamlit as st
from pymongo import MongoClient
import pandas as pd
import random

def connect_to_mongodb(mongo_uri):
    try:
        client = MongoClient(mongo_uri)
        db = client["projects"]  # Replace with your database name
        collection = db["projects"]  # Replace with your collection name
        return collection
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {e}")
        return None

def get_ten_documents(collection):
    if collection is None:
        return []
    try:
        pipeline = [
            {"$sample": {"size": 10}},
            {"$project": {"_id": 0, "project_name": 1, "winner": 1, "sum_price_agree": 1}}
        ]
        documents = list(collection.aggregate(pipeline))
        return documents
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
        return []

def display_data(documents):
    if not documents:
        st.warning("No documents found.")
    else:
        df = pd.DataFrame(documents)
        st.dataframe(df)

def get_single_document(collection):
    if collection is None:
        return None
    try:
        document = collection.find_one()
        return document
    except Exception as e:
        st.error(f"Error fetching document: {e}")
        return None

def main():
    st.title("Random MongoDB Documents")

    mongo_uri = "mongodb://localhost:27017/"

    collection = connect_to_mongodb(mongo_uri)

    documents = get_ten_documents(collection)
    display_data(documents)

    document = get_single_document(collection)
    display_data(document)

if __name__ == "__main__":
    main()