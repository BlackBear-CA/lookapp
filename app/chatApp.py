from flask import Flask, request, jsonify
import openai
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# 🔹 OpenAI API Key
OPENAI_API_KEY = "your_openai_api_key"
openai.api_key = OPENAI_API_KEY

# 🔹 Azure Blob Storage Configuration
AZURE_CONNECTION_STRING = "your_azure_connection_string"
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

# 🔹 Function to list blobs from a container
def list_blobs(container_name):
    container_client = blob_service_client.get_container_client(container_name)
    blobs = [blob.name for blob in container_client.list_blobs()]
    return blobs

# 🔹 ChatGPT Integration & Processing
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    # Check if user asks for blob data
    if "list files" in user_message.lower():
        blobs = list_blobs("$web")  # Change to desired container
        return jsonify({"reply": f"📂 Files in storage: {', '.join(blobs)}"})

    elif "submit a request" in user_message.lower():
        return jsonify({"reply": "📝 You can submit a request here: https://cs210032003bbb220fc.blob.core.windows.net/$web/submit_request.html"})

    # Otherwise, query ChatGPT
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )

    reply = response["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
