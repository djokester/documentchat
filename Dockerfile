FROM tiangolo/uvicorn-gunicorn:python3.11
COPY ./ ./
RUN pip install -r requirements.txt
ARG OPENAI_API_KEY 
ENV OPENAI_API_KEY=$OPENAI_API_KEY
CMD ["streamlit", "run", "applet.py"]