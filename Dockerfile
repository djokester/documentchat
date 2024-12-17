FROM tiangolo/uvicorn-gunicorn:python3.11
COPY ./ ./
RUN pip install -r requirements.txt
ARG GROQ_API_KEY 
ENV GROQ_API_KEY=$GROQ_API_KEY
CMD ["streamlit", "run", "applet.py"]