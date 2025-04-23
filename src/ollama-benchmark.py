################################################################################
### ollama-benckmark.py
### Copyright (c) 2025, Joshua J Hamilton
### This script will:
###   Download and test a list of models defined in the script. LLMs were 
###     selected based on their size: PaperQA2 recommends using models with 7B 
####    parameters or greater, but the models also must fit within memory (48 GB).
###   Measure runtime and speed (tokens per second) on a single query.
###   Save the results to `results/ollama_benchmark.csv`.
### After running the script, review the benchmarking results in the CSV file 
### to exclude models that are too slow for practical use.
################################################################################

################################################################################
### Import packages
################################################################################

import os
import pandas as pd
import requests
import requests.exceptions
import subprocess
import time
from tqdm import tqdm

################################################################################
### Functions
################################################################################

def create_logs_directory():
    """Create the logs directory if it doesn't exist."""
    os.makedirs("logs", exist_ok=True)
    print("Logs directory created.")

def start_ollama_server():
    """Start the Ollama server."""
    print("Starting Ollama server...")
    
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=open("logs/stdout.log", "a"),
        stderr=open("logs/stderr.log", "a")
    )
    time.sleep(5)  # Give the server time to start
    return process

def stop_ollama_server(process):
    """Stop the Ollama server."""
    print("Shutting down Ollama server...")
    process.terminate()
    process.wait()

def benchmark_model(model, prompt, ollama_server_url):
    """Benchmark a single model."""

    model_name = model["name"]
    model_parameters = model["parameters"]
    full_model_name = f"{model_name}:{model_parameters}"

    # Download the model
    print(f"Downloading model {full_model_name} ...")
    subprocess.run(["ollama", "pull", full_model_name],
                    stdout=open("logs/stdout.log", "a"),
                    stderr=open("logs/stderr.log", "a")
    )

    # Run the model with the question
    print(f"Running model {full_model_name} ...")
    try:
        response = requests.post(
            f"{ollama_server_url}/api/generate",
            json={"model": full_model_name, "prompt": prompt, "stream": False},
        )

        # Record the answer and runtime
        if response.status_code == 200:
            answer = response.json().get("response", "No response")
            runtime = response.json().get("total_duration", 0) / 10**9
            speed = (response.json().get("eval_count", 0) / response.json().get("eval_duration", 0)) * 10**9
        else:
            answer = "Error"
            runtime = 0
            speed = 0

    except requests.exceptions.Timeout:
        print(f"Model {full_model_name} timed out after 60 seconds.")
        answer = "Timeout"
        runtime = 0
        speed = 0

    # Stop the model
    print(f"Stopping model {full_model_name} ...")
    subprocess.run(["ollama", "stop", full_model_name],
                    stdout=open("logs/stdout.log", "a"),
                    stderr=open("logs/stderr.log", "a")
    )
    time.sleep(5)  # Give the server time to stop

    return {
        "Model": model_name,
        "Parameters": model_parameters,
        "Answer": answer,
        "Runtime (s)": runtime,
        "Speed (tokens/s)": speed
    }

def save_results(results, output_file):
    """Save benchmarking results to a CSV file."""
    benchmark_results = pd.DataFrame(results)
    os.makedirs("results", exist_ok=True)
    benchmark_results.to_csv(output_file, index=False)
    print(f"Benchmarking complete. Results saved to '{output_file}'.")


################################################################################
### Execution
################################################################################

def main():
    # Define the models and parameters to benchmark
    models = [
        {"name": "gemma3", "parameters": "12b"},
        {"name": "gemma3", "parameters": "27b"},
        {"name": "deepseek-r1", "parameters": "7b"},
        {"name": "deepseek-r1", "parameters": "8b"},
        {"name": "deepseek-r1", "parameters": "14b"},
        {"name": "deepseek-r1", "parameters": "32b"},
        {"name": "deepseek-r1", "parameters": "70b"},
        {"name": "deepseek-llm", "parameters": "7b"},
        {"name": "deepseek-llm", "parameters": "67b"},
        {"name": "deepseek-v2", "parameters": "16b"},
        {"name": "llama2", "parameters": "7b"},
        {"name": "llama2", "parameters": "13b"},
        {"name": "llama2", "parameters": "70b"},
        {"name": "llama3", "parameters": "8b"},
        {"name": "llama3", "parameters": "70b"},
        {"name": "llama3.1", "parameters": "8b"},
        {"name": "llama3.1", "parameters": "70b"},
        {"name": "llama3.3", "parameters": "70b"},
    ]

    # Define the question to ask
    prompt = "In molecular biology, what are the four canonical bases of DNA?"

    # Create the logs directory
    create_logs_directory()

    # Start the Ollama server
    ollama_process = start_ollama_server()
    ollama_server_url = "http://localhost:11434"  # Default Ollama server address

    # Create a list to store benchmarking outputs
    benchmark_results_list = []

    try:
        # Use tqdm to display progress
        for model in tqdm(models, desc="Benchmarking Models"):
            for i in range(3):
                result = benchmark_model(model, prompt, ollama_server_url)
                benchmark_results_list.append(result)
                time.sleep(5)  # Sleep for 5 seconds between queries
    finally:
        # Shut down the Ollama server
        stop_ollama_server(ollama_process)

    # Save the benchmarking results to a CSV file
    save_results(benchmark_results_list, "results/ollama_benchmark.csv")

if __name__ == "__main__":
    main()