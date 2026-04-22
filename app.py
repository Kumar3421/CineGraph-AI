import streamlit as st
import pandas as pd
import os
import plotly.express as px
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="CineGraph AI — Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2d3142;
    }
    h1, h2, h3 {
        color: #00d4ff;
    }
    </style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Neo4j Driver Connection
@st.cache_resource
def get_neo4j_driver():
    if not NEO4J_URI or not NEO4J_PASSWORD:
        st.error("Missing Neo4j credentials in .env file!")
        return None
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

driver = get_neo4j_driver()

def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params)
        return pd.DataFrame([r.values() for r in result], columns=result.keys())

# Sidebar
st.sidebar.image("https://neo4j.com/wp-content/uploads/neo4j-logo-2020-1.png", width=200)
st.sidebar.title("CineGraph AI")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigation", ["Overview", "Director Deep Dive", "Genre Trends", "Collaboration Network"])

st.title("🎬 CineGraph AI Intelligence Dashboard")
st.markdown("Exploring the relationships within 100,000 movies (1950-2026).")

if menu == "Overview":
    st.header("📊 Global Knowledge Graph Stats")
    
    # Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with st.spinner("Fetching stats..."):
        stats_query = """
        MATCH (m:Movie) WITH count(m) AS movies
        MATCH (d:Director) WITH movies, count(d) AS directors
        MATCH (a:Actor) WITH movies, directors, count(a) AS actors
        MATCH ()-[r]->() WITH movies, directors, actors, count(r) AS rels
        RETURN movies, directors, actors, rels
        """
        stats_df = run_query(stats_query)
        
        if not stats_df.empty:
            col1.metric("Total Movies", f"{stats_df['movies'][0]:,}")
            col2.metric("Directors", f"{stats_df['directors'][0]:,}")
            col3.metric("Actors", f"{stats_df['actors'][0]:,}")
            col4.metric("Relationships", f"{stats_df['rels'][0]:,}")

    st.markdown("---")
    
    # Top Genres Chart
    st.subheader("🎭 Top Genres by Volume")
    genre_query = """
    MATCH (g:Genre)<-[:IN_GENRE]-(m:Movie)
    RETURN g.name AS Genre, count(m) AS Count
    ORDER BY Count DESC LIMIT 10
    """
    genre_df = run_query(genre_query)
    fig_genre = px.bar(genre_df, x='Genre', y='Count', color='Count', color_continuous_scale='Blues', template='plotly_dark')
    st.plotly_chart(fig_genre, use_container_width=True)

elif menu == "Director Deep Dive":
    st.header("🎥 Director Performance Analysis")
    director_name = st.text_input("Enter Director Name", "Christopher Nolan")
    
    if director_name:
        query = """
        MATCH (d:Director {name: $name})-[:DIRECTED]->(m:Movie)
        RETURN m.title AS Title, m.release_year AS Year, m.imdb_rating AS Rating, 
               m.revenue_million AS Revenue_M, m.roi_pct AS ROI
        ORDER BY Year DESC
        """
        df = run_query(query, {"name": director_name})
        
        if not df.empty:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(df, use_container_width=True)
            with col2:
                avg_rating = df['Rating'].mean()
                total_rev = df['Revenue_M'].sum()
                st.metric("Avg Rating", f"{avg_rating:.2f}")
                st.metric("Total Revenue", f"${total_rev:.1f}M")
            
            st.subheader("Rating Evolution")
            fig = px.line(df, x='Year', y='Rating', markers=True, template='plotly_dark', color_discrete_sequence=['#00d4ff'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"No data found for director: {director_name}")

elif menu == "Genre Trends":
    st.header("📈 Genre Performance Through Decades")
    genre_list = run_query("MATCH (g:Genre) RETURN g.name AS Genre ORDER BY Genre")['Genre'].tolist()
    selected_genre = st.selectbox("Select Genre", genre_list)
    
    if selected_genre:
        query = """
        MATCH (g:Genre {name: $genre})<-[:IN_GENRE]-(m:Movie)-[:RELEASED_IN]->(d:Decade)
        RETURN d.name AS Decade, avg(m.imdb_rating) AS Avg_Rating, count(m) AS Movie_Count
        ORDER BY Decade
        """
        df = run_query(query, {"genre": selected_genre})
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.area(df, x='Decade', y='Movie_Count', title=f"Movies in {selected_genre}", template='plotly_dark')
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.line(df, x='Decade', y='Avg_Rating', title=f"Average Rating Trend", template='plotly_dark')
            st.plotly_chart(fig2, use_container_width=True)

elif menu == "Collaboration Network":
    st.header("🤝 Actor-Director Collaborations")
    actor_name = st.text_input("Enter Actor Name", "Brad Pitt")
    
    if actor_name:
        query = """
        MATCH (a:Actor {name: $name})-[:ACTED_IN]->(m:Movie)<-[:DIRECTED]-(d:Director)
        RETURN d.name AS Director, count(m) AS Collaborations, avg(m.imdb_rating) AS Avg_Rating
        ORDER BY Collaborations DESC
        """
        df = run_query(query, {"name": actor_name})
        if not df.empty:
            st.table(df)
            fig = px.scatter(df, x='Collaborations', y='Avg_Rating', text='Director', size='Collaborations', template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No collaborations found.")

st.sidebar.markdown("---")
st.sidebar.info("CineGraph AI is built with Neo4j Aura and Streamlit.")
