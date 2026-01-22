# MSc_Dissertation_Project
AI-Based Detection of DDoS Attacks in IoT Smart Home Environments
Overview

This project implements an AI-driven intrusion detection system for identifying Distributed Denial of Service (DDoS) attacks in an IoT-based smart home environment. The system uses Home Assistant and MQTT to simulate smart home sensor traffic and applies machine learning models to detect malicious behaviour.

Objectives

Simulate a smart home IoT environment using Home Assistant

Capture and analyse normal and DDoS network traffic

Apply unsupervised and supervised AI models for intrusion detection

Integrate trained models into a live smart home monitoring pipeline

Technologies Used

Python
Home Assistant
MQTT
Wireshark
Isolation Forest
XGBoost
Flask (REST API)

Project Structure

Normal traffic.csv – Captured normal IoT traffic

DDoS traffic.csv – Captured DDoS attack traffic

Isolation Forest Model.ipynb – Unsupervised anomaly detection model

Xgboost Model.ipynb – Supervised DDoS classification model

model_API.py – REST API for model inference

live_ddos_detection.py – Live MQTT-based detection script

Home Assistant Sensors Simulation.ipynb – Sensor data simulation

How It Works

IoT sensor data is generated in Home Assistant and transmitted via MQTT

Network traffic is captured and preprocessed

Models are trained using extracted traffic features

Trained models are deployed via a Python API

Live sensor traffic is analysed in real time for anomalies or attacks

Key Findings

Isolation Forest effectively detects anomalies in offline analysis

XGBoost achieves high accuracy on labelled datasets

Live detection flagged all traffic as normal due to simulated data limitations

Future Improvements

Train models using real-world IoT traffic

Improve feature alignment between training and live inference

Implement automated response actions in Home Assistant

Author

Joseph Owolabi


This project is for academic and research purposes.
