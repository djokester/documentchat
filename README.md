# DocumentChat

Streamlit App to Chat with Documents. Can try with other datasets as well. 
Faces issues with complex queries on JSoN type columns but can answer basic questions asking to list and filter. 
Usage

```
pip install -r requirements.txt
export OPENAI_API_KEY=""
streamlit run applet.py
```

There is a docker container as well. 

```
export OPENAI_API_KEY=""
docker build -t docchat .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8501:8501 docchat
```
