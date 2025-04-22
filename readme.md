# Langraph Interview Agent

This project consists of a backend agent API and a frontend application.

## Getting Started

Follow these steps to get the project up and running.

### Prerequisites

* Python

* Node.js and npm

* MongoDB instance

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/nikhilcramakrishnan/interview-agent-langgraph.git
   cd interview-agent-langgraph

   ```

2. **Backend Agent API:**

   Install the required Python packages from the root directory. It's recommended to use a virtual environment:

   ```
   # Create a virtual environment
   python -m venv venv
   # Activate the virtual environment
   # On Windows:
   # .\venv\Scripts\activate
   # On macOS/Linux:
   # source venv/bin/activate

   pip install -r requirements.txt

   ```

3. **Frontend Application:**

   Navigate to the `frontend` directory:

   ```
   cd frontend

   ```

   Install the Node.js dependencies:

   ```
   npm install

   ```

### Configuration

**Backend Agent API:**

Create a `.env` file in the `agent` directory with the following variables:

```
GOOGLE_API_KEY=your_google_api_key
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB_NAME=your_database_name
NUM_QUESTIONS=number_of_questions

```

Replace the placeholder values with your actual Google API key, MongoDB connection URI, database name, and the desired number of questions.

### Running the Project

1. **Start the Agent API:**

   From the root directory of the project, run the following command:

   ```
   uvicorn agent.api:api --reload

   ```

   This will start the FastAPI development server with auto-reloading enabled.

2. **Start the Frontend Application:**

   Navigate to the `frontend` directory if you are not already there and run the following command:

   ```
   npm start

   ```

   This will start the React development server. The frontend application should open in your default browser.
