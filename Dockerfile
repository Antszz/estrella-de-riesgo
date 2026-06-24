FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py datos.py estrella.py estrella_plotly.py car_insurance_claim.csv ./

ENV PORT=7860
ENV MPLCONFIGDIR=/tmp/matplotlib
EXPOSE 7860

CMD ["python", "app.py"]
