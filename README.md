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

![image](https://github.com/user-attachments/assets/7e7c8c3a-07b7-40b6-96dd-a81fa2940388)

## What is the distribution of movie release years?
![image](https://github.com/user-attachments/assets/556a7edd-84db-4b0a-867d-fba35aa558f3)


## Which are the top 10 highest-grossing movies of all time?
![image](https://github.com/user-attachments/assets/d1eeb02e-4c4b-43a6-8487-cd4e2165f1d4)

## What is the average runtime of movies by decade?
![image](https://github.com/user-attachments/assets/e3a05d83-fdc6-4958-9818-6f5ca899cb52)


## How does the popularity of movies correlate with their revenue?
![image](https://github.com/user-attachments/assets/5a5b70de-a782-4b4e-8422-d2390e780a56)


## What are the trends in movie budgets and revenues over time?
![image](https://github.com/user-attachments/assets/82610f73-f5a5-40da-bd8d-d60e91a0e2cb)


## Do movies with higher vote counts tend to have higher average ratings?
![image](https://github.com/user-attachments/assets/4eaf75b1-d5b2-499a-9c92-5d49aaded96f)


## Which languages dominate the movie dataset? Provide a pie chart
![image](https://github.com/user-attachments/assets/1037affb-0411-4d05-954e-d185c8850704)

## How does runtime affect movie popularity?
![image](https://github.com/user-attachments/assets/8a0b4caf-8b07-4995-9d88-9fffd65a98ad)
