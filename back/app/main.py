import logging
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import uvicorn
from starlette.middleware.cors import CORSMiddleware

# from cluster.create_csv_labeled_data import labeled_jsons_to_df
from back.cluster.create_all_data import file_2_df
from back.cluster.w2v import file_2_vectors
from back.sentiment.sent_label import json_to_sentiment
from back.cluster.generate_clusters import generate_k_means_clusters, clusters_2_df
from back.sentiment.bad_answers import bad_answers


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_json(file: UploadFile = File()):
    try:
        contents = file.file.read()
        file_location = "data/" + file.filename
        with open(file_location, "wb") as f:
            f.write(contents)
    except Exception:
        return {"message": f"There was an error uploading the file {Exception}"}

    vectors, model = file_2_vectors(file_location)
    s_score, kmeans = generate_k_means_clusters(vectors)
    df_text = file_2_df(file_location)
    clustered = clusters_2_df(vectors, kmeans, model, df_text)
    bad_ans = bad_answers(df_text)
    bad_ans.to_csv("data/bad_answers.csv", index=False)
    # logging.warning(bad_ans)
    # sentiment_list = json_to_sentiment(file_location)

    # clustered['sentiment'] = sentiment_list
    with open("data/clustered.json", "w", encoding="utf8") as f:
        clustered.to_json(f, force_ascii=False)

    return FileResponse("data/clustered.json")


@app.get("/get_img")
async def show_result():
    return FileResponse("test.jpg")


@app.get("/get_errors")
async def get_errors():
    bad_ans = pd.read_csv("data/bad_answers.csv")

    with open("data/bad_ans.json", "w", encoding="utf8") as f:
        bad_ans.to_json(f, force_ascii=False)

    return FileResponse("data/bad_ans.json")


if __name__ == "__main__":
    # Run server using given host and port
    uvicorn.run(app, host="localhost", port=8080)
