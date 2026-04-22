# 🎬 CineGraph AI — Global Cinema Intelligence

CineGraph AI is a sophisticated Knowledge Graph agent built for the **Neo4j Aura Agent Hackathon**. It transforms a dataset of 100,000 movies (1950–2026) into a reasoning engine that answers complex, multi-hop questions about the film industry.

## 🚀 Features

- **Graph-Powered Reasoning**: Uses multi-hop traversals to answer "why" and "how" questions, not just "what".
- **Intelligent Tools**: 6 custom Cypher Template tools for career analysis, collaboration networks, and trend forecasting.
- **Aura Agent Integration**: Fully configured for the Neo4j Aura Agent console.
- **Live Streamlit Dashboard**: A custom web interface for exploring the graph data visually.

## 📊 Knowledge Graph Schema

The graph models the following entities and relationships:
- **Nodes**: `Movie`, `Director`, `Actor`, `Genre`, `Country`, `Language`, `Decade`, `StreamingPlatform`.
- **Relationships**: `DIRECTED`, `ACTED_IN`, `IN_GENRE`, `PRODUCED_IN`, `RELEASED_IN`, `AVAILABLE_ON`.

## 🛠️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd neo4j
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file based on `.env.example` and add your Neo4j Aura credentials.

4. **Run the Streamlit App**:
   ```bash
   streamlit run app.py
   ```

## 📂 Project Structure

- `app.py`: Streamlit web application.
- `import_movies.py`: Data ingestion script for Neo4j Aura.
- `AGENT_CONFIG.md`: Complete guide for setting up the Aura Agent.
- `global_movies_dataset_1950_2026.csv`: The core dataset (100k rows).

## 🏆 Hackathon Submission

This project is submitted to the **Neo4j Aura Agent Hackathon**. It demonstrates the power of combining LLMs with structured Knowledge Graphs at scale.

---
Built with ❤️ for the Neo4j Community.
