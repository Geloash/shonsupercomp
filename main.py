from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import pandas as pd
import plotly.express as px
import numpy as np
from google.cloud import firestore, storage
import uuid
import io
from datetime import datetime
import json
import os
from google.oauth2 import service_account

# Глобальная константа для секретного кода
SECRET_CODE = "1701"

# Инициализация Firestore и GCS
try:
    gcp_service_account_info_json_str = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")
    if not gcp_service_account_info_json_str:
        raise ValueError("Environment variable GCP_SERVICE_ACCOUNT_KEY is not set.")
    gcp_service_account_info = json.loads(gcp_service_account_info_json_str)
    credentials = service_account.Credentials.from_service_account_info(gcp_service_account_info)
    db = firestore.Client(credentials=credentials, database='superpcdatab')
    storage_client = storage.Client(credentials=credentials)
    bucket_name = "supercomputer-graphs-123"  # Замени на имя твоего бакета
    bucket = storage_client.bucket(bucket_name)
    print("Firestore and GCS clients initialized.")
except Exception as e:
    print(f"FATAL ERROR: Could not initialize clients: {e}")
    raise Exception(f"Failed to initialize: {e}. Ensure GCP_SERVICE_ACCOUNT_KEY env var is set.")

collection = db.collection('supercomputer_graphs')
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def get_home():
    image_url1 = "https://previews.dropbox.com/p/thumb/ACsXIJT6uDu3_9KF1hr8G0MW90EFfUZH1nfIjdZCqgmVEqfr41XrwcPUuah8TnkAu64d9LoQ4LxLq8Pv_C38A44qB6L2jGhSXWUi1ZxKjEfxXl5DSrH7X_2tJ1q0rHf7kJwsCAgZbKhSFEmiHWwklx3oXUHaMeKW0gFg6EQNb5Gy09keMAezN8TPgXishPeEesLpbRgUVXDecdbAIYSabJND6u6VcAHsVixsyZ2ITFZE5YNXS_AJaKi2fRFtd8OFOUMwPz56BkTcOnwiulsYerjTCUCJ8cVTdY7aOzfOqxYqVfBJXXRup7t11rsEkZrIk9A/p.png"
    image_url2 = "https://previews.dropbox.com/p/thumb/ACvr2J7HqCiwFEp0LlCa55sCjdwUd_6XszKMD0kBcbjuSbxaWYHMuhITYEcVATsZNlNPOEX4mXANgJ_2ZwcZeGn9iPyubpllPLiWHkN60b0A9jSJRyCOMpcrwkzNqY0frwIpPvI8YNecE2sUElA5bcVLANYIrt-MYCiCy9E_6r7h6LABMArCl0LV-SNi-dttrGv0FTe-Uv40zL-JoFaAMB7yyL1FQTiv-5Mmi4Aeeu9ucgIJ-tnM_64k6-mXrICOS7VMTOkX7kliBSj_6jge1GgsnCxX_798GwNbDioQxdNdc8uGe3cKnK2PDZmvsXs6VH4D-TVP6djK27PgEYIsPoh5/p.png"

    html_header = """
    <html>
        <head>
            <title>Supercomputer Graphs</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background-color: #f8f9fa; color: #343a40; }
                .container { max-width: 960px; margin: auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                h1, h2 { color: #007bff; margin-bottom: 20px; }
                .form-control { border-radius: 5px; }
                .btn-primary { background-color: #007bff; border-color: #007bff; transition: background-color 0.3s ease; }
                .btn-primary:hover { background-color: #0056b3; border-color: #0056b3; }
                .image-container { display: flex; justify-content: center; margin-top: 20px; flex-wrap: wrap; }
                .image-item, .graph-item { max-width: 45%; height: auto; margin: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: transform 0.2s ease; cursor: pointer; }
                .image-item:hover, .graph-item:hover { transform: scale(1.02); }
                .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100vh; background-color: rgba(0, 0, 0, 0.9); justify-content: center; align-items: center; z-index: 1050; }
                .modal-content { width: auto; height: auto; max-width: 90vw; max-height: 90vh; object-fit: contain; border-radius: 8px; background-color: transparent; }
                .modal-graph { width: 100%; height: 100%; border: none; }
                .list-group-item { background-color: #e9ecef; border: 1px solid #dee2e6; margin-bottom: 5px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }
                .list-group-item a { color: #007bff; text-decoration: none; font-weight: bold; flex-grow: 1; padding: 10px 15px; }
                .list-group-item a:hover { text-decoration: underline; }
                .modal-buttons { position: absolute; top: 50%; width: 100%; display: flex; justify-content: space-between; padding: 0 20px; z-index: 1060; }
                .modal-buttons button { background: rgba(0,0,0,0.5); border: none; color: white; cursor: pointer; padding: 15px; border-radius: 50%; font-size: 20px; transition: background-color 0.3s ease; }
                .modal-buttons button:hover { background: rgba(0,0,0,0.8); }
                .close-button { position: absolute; top: 20px; right: 30px; color: white; font-size: 35px; font-weight: bold; cursor: pointer; z-index: 1060; }
                .close-button:hover, .close-button:focus { color: #bbb; text-decoration: none; cursor: pointer; }
                .code-modal-content { background-color: #fefefe; margin: auto; padding: 30px; border: 1px solid #888; width: 80%; max-width: 400px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); text-align: center; position: relative; }
                .code-modal-content h3 { color: #343a40; margin-bottom: 20px; }
                .code-modal-content input[type="password"] { width: calc(100% - 20px); padding: 10px; margin-bottom: 15px; border: 1px solid #ced4da; border-radius: 5px; text-align: center; font-size: 1.2em; }
                .code-modal-content button { background-color: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 1em; transition: background-color 0.3s ease; }
                .code-modal-content button:hover { background-color: #218838; }
                .code-modal-error { color: #dc3545; margin-top: 10px; font-size: 0.9em; }
                .delete-btn { background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; font-size: 0.8em; margin-left: 10px; transition: background-color 0.3s ease; }
                .delete-btn:hover { background-color: #c82333; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="mt-4 text-center">Загрузить данные суперкомпьютеров</h1>
                <form id="uploadForm" method="post" enctype="multipart/form-data">
                    <div class="input-group mb-3">
                        <input type="file" name="file" accept=".csv" class="form-control" id="csvFile" required>
                        <button type="button" class="btn btn-primary" id="uploadButton">Загрузить</button>
                    </div>
                </form>
                <h2 class="mt-4 text-center">История графиков</h2>
                <ul class="list-group" id="graphList">
    """

    docs = collection.order_by('timestamp', direction=firestore.Query.DESCENDING).get()
    list_items = ""
    graph_ids = []
    for doc in docs:
        data = doc.to_dict()
        graph_ids.append(data['id'])
        try:
            display_timestamp = datetime.fromisoformat(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            display_timestamp = data['timestamp']
        list_items += f"""
                    <li id="graph-{data['id']}" class="list-group-item">
                        <a href="#" onclick="openGraphModal('{data['id']}')">График от {display_timestamp}</a>
                        <button class="delete-btn" onclick="openCodeModal('delete', '{data['id']}')">Удалить</button>
                    </li>
        """

    html_footer = f"""
                </ul>
                <div class="image-container">
                    <img src="{image_url1}" alt="Image 1" class="image-item" onclick="openModal('{image_url1}')">
                    <img src="{image_url2}" alt="Image 2" class="image-item" onclick="openModal('{image_url2}')">
                </div>
            </div>

            <div id="myModal" class="modal">
                <span class="close-button" onclick="closeModal()">×</span>
                <img id="modalImage" class="modal-content" onclick="closeModal()">
            </div>

            <div id="graphModal" class="modal">
                <span class="close-button" onclick="closeGraphModal()">×</span>
                <div class="modal-buttons">
                    <button onclick="changeGraph(-1)">❮</button>
                    <button onclick="changeGraph(1)">❯</button>
                </div>
                <iframe id="graphContent" class="modal-content modal-graph"></iframe>
            </div>

            <div id="codeModal" class="modal">
                <div class="code-modal-content">
                    <span class="close-button" onclick="closeCodeModal()">×</span>
                    <h3 id="codeModalTitle">Введите код доступа</h3>
                    <input type="password" id="accessCodeInput" placeholder="Код доступа">
                    <div id="codeError" class="code-modal-error"></div>
                    <button id="submitCodeButton">Подтвердить</button>
                </div>
            </div>

            <script>
                let graphIds = """ + json.dumps(graph_ids) + """;
                let currentGraphIndex = 0;
                let currentAction = null;
                let currentGraphToDeleteId = null;

                document.addEventListener('DOMContentLoaded', function() {
                    const uploadButton = document.getElementById('uploadButton');
                    const codeModal = document.getElementById('codeModal');
                    const codeModalTitle = document.getElementById('codeModalTitle');
                    const accessCodeInput = document.getElementById('accessCodeInput');
                    const submitCodeButton = document.getElementById('submitCodeButton');
                    const codeError = document.getElementById('codeError');
                    const csvFile = document.getElementById('csvFile');

                    uploadButton.addEventListener('click', function() {
                        if (!csvFile.files.length) {
                            alert('Пожалуйста, выберите CSV файл для загрузки.');
                            return;
                        }
                        openCodeModal('upload');
                    });

                    function openCodeModal(action, graphId = null) {
                        currentAction = action;
                        currentGraphToDeleteId = graphId;
                        codeModal.style.display = 'flex';
                        accessCodeInput.value = '';
                        codeError.textContent = '';
                        document.body.style.overflow = 'hidden';
                        codeModalTitle.textContent = action === 'upload' ? 'Введите код для загрузки' : 'Введите код для удаления';
                    }
                    window.openCodeModal = openCodeModal;

                    function closeCodeModal() {
                        codeModal.style.display = 'none';
                        document.body.style.overflow = 'auto';
                        currentAction = null;
                        currentGraphToDeleteId = null;
                    }
                    window.closeCodeModal = closeCodeModal;

                    submitCodeButton.addEventListener('click', async function() {
                        const accessCode = accessCodeInput.value;
                        if (!accessCode) {
                            codeError.textContent = 'Пожалуйста, введите код.';
                            return;
                        }

                        if (currentAction === 'upload') {
                            const file = csvFile.files[0];
                            const formData = new FormData();
                            formData.append('file', file);
                            formData.append('code', accessCode);

                            try {
                                const response = await fetch('/upload', {
                                    method: 'POST',
                                    body: formData
                                });

                                if (response.ok) {
                                    alert('Файл успешно загружен и график создан!');
                                    window.location.href = '/';
                                } else {
                                    const errorData = await response.json();
                                    codeError.textContent = errorData.detail || 'Неверный код или ошибка сервера.';
                                }
                            } catch (error) {
                                console.error('Error uploading file:', error);
                                codeError.textContent = 'Ошибка сети или сервера.';
                            }
                        } else if (currentAction === 'delete') {
                            try {
                                const response = await fetch(`/graph/${currentGraphToDeleteId}`, {
                                    method: 'DELETE',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({ code: accessCode })
                                });

                                if (response.ok) {
                                    alert('График успешно удален!');
                                    const listItem = document.getElementById(`graph-${currentGraphToDeleteId}`);
                                    if (listItem) {
                                        listItem.remove();
                                        graphIds = graphIds.filter(id => id !== currentGraphToDeleteId);
                                        if (graphIds.length > 0) {
                                            if (currentGraphIndex >= graphIds.length) {
                                                currentGraphIndex = graphIds.length - 1;
                                            }
                                        } else {
                                            currentGraphIndex = -1; // Нет графиков
                                        }
                                    }
                                    closeCodeModal();
                                } else {
                                    const errorData = await response.json();
                                    codeError.textContent = errorData.detail || 'Неверный код или ошибка сервера.';
                                }
                            } catch (error) {
                                console.error('Error deleting graph:', error);
                                codeError.textContent = 'Ошибка сети или сервера при удалении.';
                            }
                        }
                    });
                });

                function openModal(imageUrl) {
                    var modal = document.getElementById("myModal");
                    var modalImage = document.getElementById("modalImage");
                    modal.style.display = "flex";
                    modalImage.src = imageUrl;
                    document.body.style.overflow = 'hidden';
                    console.log("Opening modal with image:", imageUrl);
                }
                function closeModal() {
                    var modal = document.getElementById("myModal");
                    modal.style.display = "none";
                    document.body.style.overflow = 'auto';
                }
                function openGraphModal(graphId) {
                    currentGraphIndex = graphIds.indexOf(graphId);
                    loadGraph();
                    document.body.style.overflow = 'hidden';
                }
                function loadGraph() {
                    var modal = document.getElementById("graphModal");
                    var graphContent = document.getElementById("graphContent");
                    if (currentGraphIndex >= 0 && currentGraphIndex < graphIds.length) {
                        fetch(`/graph/${graphIds[currentGraphIndex]}`)
                            .then(response => {
                                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                                return response.text();
                            })
                            .then(html => {
                                graphContent.srcdoc = html;
                                modal.style.display = "flex";
                                console.log("Graph loaded successfully for ID:", graphIds[currentGraphIndex]);
                            })
                            .catch(error => console.error('Error loading graph:', error));
                    } else {
                        console.log("Invalid graph index:", currentGraphIndex);
                    }
                }
                function changeGraph(direction) {
                    currentGraphIndex += direction;
                    if (currentGraphIndex < 0) currentGraphIndex = graphIds.length - 1;
                    if (currentGraphIndex >= graphIds.length) currentGraphIndex = 0;
                    loadGraph();
                }
                document.getElementById("graphModal").onclick = function(event) {
                    if (event.target === this || event.target.tagName === 'IFRAME') {
                        closeGraphModal();
                    }
                };
                function closeGraphModal() {
                    var modal = document.getElementById("graphModal");
                    modal.style.display = "none";
                    document.body.style.overflow = 'auto';
                }
                document.addEventListener('keydown', function(event) {
                    if (event.key === 'Escape') {
                        closeGraphModal();
                        closeModal();
                        closeCodeModal();
                    }
                });
            </script>
        </body>
    </html>
    """

    return HTMLResponse(content=html_header + list_items + html_footer)

@app.get("/api/graph_ids")
async def get_graph_ids_api():
    docs = collection.order_by('timestamp', direction=firestore.Query.DESCENDING).get()
    graph_ids = [doc.id for doc in docs]
    return {"graph_ids": graph_ids}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), code: str = Form(...)):
    if code != SECRET_CODE:
        raise HTTPException(status_code=401, detail="Неверный код доступа")
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Только CSV файлы разрешены")

        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        print("DataFrame before cleaning:")
        print(df.info())
        print(df.head())

        required_columns = ['Supercomputer', 'EFLOPS', 'Power (GW)', 'Units', 'Label']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise HTTPException(status_code=400, detail=f"Неверная структура CSV. Отсутствуют колонки: {', '.join(missing_cols)}. Требуются: " + ", ".join(required_columns))

        if 'EFLOPS' in df.columns:
            df['EFLOPS'] = pd.to_numeric(df['EFLOPS'], errors='coerce')
        if 'Power (GW)' in df.columns:
            df['Power (GW)'] = pd.to_numeric(df['Power (GW)'], errors='coerce')

        initial_rows = len(df)
        df.dropna(subset=['EFLOPS', 'Power (GW)'], inplace=True)
        dropped_rows_critical = initial_rows - len(df)
        if dropped_rows_critical > 0:
            print(f"Dropped {dropped_rows_critical} rows due to missing/invalid EFLOPS or Power (GW).")

        if 'Units' in df.columns:
            df['Units'] = df['Units'].fillna('')

        print("DataFrame after cleaning:")
        print(df.info())
        print(df.head())

        current_year = datetime.now().year
        fig = px.scatter(df, x='Supercomputer', y='EFLOPS', size='Power (GW)', text='EFLOPS',
                        hover_data=['Label', 'Units'],
                        size_max=60,
                        title=f'Сравнение суперкомпьютеров ({current_year})')
        fig.update_traces(textposition='top center')
        fig.update_yaxes(type='log', range=[np.log10(0.1), np.log10(35)])

        graph_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        temp_filename = f"/tmp/{graph_id}.html"
        fig.write_html(temp_filename)

# Загрузка в GCS
blob = bucket.blob(f"graphs/{graph_id}.html")
print(f"Uploading to: graphs/{graph_id}.html")
try:
    blob.upload_from_filename(temp_filename)
    print(f"Uploaded, checking existence: {blob.exists()}")
    blob.make_public()
    public_url = blob.public_url
    print(f"Public URL: {public_url}")
except Exception as e:
    print(f"Error uploading to GCS: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Ошибка загрузки в GCS: {str(e)}")

        # Удаление временного файла
        os.remove(temp_filename)

        # Сохранение в Firestore
        doc_ref = collection.document(graph_id)
        doc_ref.set({
            'id': graph_id,
            'timestamp': timestamp,
            'graph_url': public_url
        })
        print(f"Graph uploaded: {public_url}")
        return RedirectResponse(url="/", status_code=303)

    except HTTPException as he:
        print(f"HTTP Error: {he.detail}")
        raise he
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка при загрузке или обработке файла: {str(e)}")

@app.delete("/graph/{graph_id}")
async def delete_graph(graph_id: str, code: str = Form(...)):
    if code != SECRET_CODE:
        raise HTTPException(status_code=401, detail="Неверный код доступа")
    try:
        doc_ref = collection.document(graph_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="График не найден в базе данных")

        # Удаление из GCS
        blob = bucket.blob(f"graphs/{graph_id}.html")
        if blob.exists():
            blob.delete()
            print(f"Graph file {graph_id}.html deleted from GCS.")

        doc_ref.delete()
        print(f"Document {graph_id} deleted from Firestore.")
        return RedirectResponse(url="/", status_code=303)

    except HTTPException as he:
        print(f"HTTP Error in delete_graph: {he.detail}")
        raise he
    except Exception as e:
        print(f"Error in delete_graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении графика: {str(e)}")

@app.get("/graph/{graph_id}")
async def get_graph(graph_id: str):
    try:
        doc_ref = collection.document(graph_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="График не найден в базе данных")
        data = doc.to_dict()
        public_url = data.get('graph_url')
        if not public_url:
            raise HTTPException(status_code=500, detail="Публичный URL графика не найден в Firestore")
        # Перенаправляем на публичный URL
        return RedirectResponse(url=public_url)
    except HTTPException as he:
        print(f"HTTP Error in get_graph: {he.detail}")
        raise he
    except Exception as e:
        print(f"Error in get_graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки графика: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
