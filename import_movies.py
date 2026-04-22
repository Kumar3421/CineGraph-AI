"""
CineGraph AI — Neo4j Aura Data Import Script
=============================================
Imports the Global Movies Dataset (100K movies, 1950-2026) into Neo4j Aura
as a rich knowledge graph for the Aura Agent Hackathon.

Usage:
    1. Copy .env.example to .env and fill in your Aura credentials
    2. pip install -r requirements.txt
    3. python import_movies.py
"""

import os
import csv
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

CSV_FILE = os.path.join(os.path.dirname(__file__), "global_movies_dataset_1950_2026.csv")
BATCH_SIZE = 500


def create_constraints(session):
    """Create uniqueness constraints and indexes for fast lookups."""
    constraints = [
        "CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.movie_id IS UNIQUE",
        "CREATE CONSTRAINT director_name IF NOT EXISTS FOR (d:Director) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT actor_name IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE",
        "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
        "CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT language_name IF NOT EXISTS FOR (l:Language) REQUIRE l.name IS UNIQUE",
        "CREATE CONSTRAINT decade_name IF NOT EXISTS FOR (d:Decade) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (sp:StreamingPlatform) REQUIRE sp.name IS UNIQUE",
    ]
    for cypher in constraints:
        try:
            session.run(cypher)
            print(f"  ✓ {cypher.split('REQUIRE')[0].strip()}")
        except Exception as e:
            print(f"  ⚠ Constraint may already exist: {e}")

    # Additional indexes for common query patterns
    indexes = [
        "CREATE INDEX movie_year IF NOT EXISTS FOR (m:Movie) ON (m.release_year)",
        "CREATE INDEX movie_rating IF NOT EXISTS FOR (m:Movie) ON (m.imdb_rating)",
        "CREATE INDEX movie_title IF NOT EXISTS FOR (m:Movie) ON (m.title)",
        "CREATE INDEX movie_blockbuster IF NOT EXISTS FOR (m:Movie) ON (m.blockbuster_flag)",
        "CREATE INDEX movie_franchise IF NOT EXISTS FOR (m:Movie) ON (m.franchise_flag)",
    ]
    for cypher in indexes:
        try:
            session.run(cypher)
            print(f"  ✓ {cypher.split('FOR')[0].strip()}")
        except Exception as e:
            print(f"  ⚠ Index may already exist: {e}")


def parse_float(val, default=0.0):
    try:
        return float(val) if val else default
    except (ValueError, TypeError):
        return default


def parse_int(val, default=0):
    try:
        return int(float(val)) if val else default
    except (ValueError, TypeError):
        return default


def read_csv_rows(filepath):
    """Read all rows from CSV into a list of dicts."""
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def import_batch(session, batch):
    """Import a batch of movie rows using a single UNWIND query."""
    records = []
    for row in batch:
        # Split pipe-separated genres
        genres = [g.strip() for g in row.get("genre", "").split("|") if g.strip()]

        records.append({
            "movie_id": parse_int(row.get("movie_id")),
            "title": row.get("title", "").strip(),
            "release_year": parse_int(row.get("release_year")),
            "decade": str(row.get("decade", "")).strip() + "s",  # e.g., "2000" -> "2000s"
            "runtime_min": parse_int(row.get("runtime_min")),
            "genres": genres,
            "subgenre": row.get("subgenre", "").strip(),
            "director": row.get("director", "").strip(),
            "lead_actor": row.get("lead_actor", "").strip(),
            "lead_actress": row.get("lead_actress", "").strip(),
            "country": row.get("country", "").strip(),
            "language": row.get("language", "").strip(),
            "imdb_rating": parse_float(row.get("imdb_rating")),
            "votes": parse_int(row.get("votes")),
            "budget_million": parse_float(row.get("budget_million")),
            "marketing_budget_million": parse_float(row.get("marketing_budget_million")),
            "revenue_million": parse_float(row.get("revenue_million")),
            "roi_pct": parse_float(row.get("roi_pct")),
            "popularity_score": parse_float(row.get("popularity_score")),
            "metascore": parse_int(row.get("metascore")),
            "audience_score": parse_int(row.get("audience_score")),
            "streaming_platform": row.get("streaming_platform", "").strip(),
            "award_nominations": parse_int(row.get("award_nominations")),
            "award_wins": parse_int(row.get("award_wins")),
            "top_100_prob": parse_float(row.get("top_100_prob")),
            "blockbuster_flag": parse_int(row.get("blockbuster_flag")),
            "franchise_flag": parse_int(row.get("franchise_flag")),
        })

    cypher = """
    UNWIND $records AS row

    // Create Movie node
    MERGE (m:Movie {movie_id: row.movie_id})
    SET m.title = row.title,
        m.release_year = row.release_year,
        m.runtime_min = row.runtime_min,
        m.subgenre = row.subgenre,
        m.imdb_rating = row.imdb_rating,
        m.votes = row.votes,
        m.budget_million = row.budget_million,
        m.marketing_budget_million = row.marketing_budget_million,
        m.revenue_million = row.revenue_million,
        m.roi_pct = row.roi_pct,
        m.popularity_score = row.popularity_score,
        m.metascore = row.metascore,
        m.audience_score = row.audience_score,
        m.award_nominations = row.award_nominations,
        m.award_wins = row.award_wins,
        m.top_100_prob = row.top_100_prob,
        m.blockbuster_flag = row.blockbuster_flag,
        m.franchise_flag = row.franchise_flag

    // Create Director + relationship
    MERGE (d:Director {name: row.director})
    MERGE (d)-[:DIRECTED]->(m)

    // Create Lead Actor + relationship
    MERGE (a1:Actor {name: row.lead_actor})
    MERGE (a1)-[:ACTED_IN {role: 'lead_actor'}]->(m)

    // Create Lead Actress + relationship
    MERGE (a2:Actor {name: row.lead_actress})
    MERGE (a2)-[:ACTED_IN {role: 'lead_actress'}]->(m)

    // Create Country + relationship
    MERGE (c:Country {name: row.country})
    MERGE (m)-[:PRODUCED_IN]->(c)

    // Create Language + relationship
    MERGE (l:Language {name: row.language})
    MERGE (m)-[:IN_LANGUAGE]->(l)

    // Create Decade + relationship
    MERGE (dec:Decade {name: row.decade})
    MERGE (m)-[:RELEASED_IN]->(dec)

    // Create Streaming Platform + relationship
    MERGE (sp:StreamingPlatform {name: row.streaming_platform})
    MERGE (m)-[:AVAILABLE_ON]->(sp)

    // Create Genre nodes + relationships (multi-genre support)
    WITH m, row
    UNWIND row.genres AS genre_name
    MERGE (g:Genre {name: genre_name})
    MERGE (m)-[:IN_GENRE]->(g)
    """

    session.run(cypher, records=records)


def main():
    print("=" * 60)
    print("  CineGraph AI — Neo4j Aura Data Import")
    print("=" * 60)
    print()

    # Validate credentials
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("❌ ERROR: Missing Neo4j credentials!")
        print("   Copy .env.example to .env and fill in your Aura credentials.")
        print("   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io")
        print("   NEO4J_USERNAME=neo4j")
        print("   NEO4J_PASSWORD=your-password")
        return

    print(f"📡 Connecting to: {NEO4J_URI}")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    # Verify connectivity
    try:
        driver.verify_connectivity()
        print("✅ Connected to Neo4j Aura!\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # Step 1: Create constraints and indexes
    print("📋 Step 1: Creating constraints and indexes...")
    with driver.session() as session:
        create_constraints(session)
    print()

    # Step 2: Read CSV
    print(f"📂 Step 2: Reading CSV from {CSV_FILE}...")
    rows = read_csv_rows(CSV_FILE)
    total = len(rows)
    print(f"   Found {total:,} movies to import.\n")

    # Step 3: Batch import
    print(f"🚀 Step 3: Importing movies in batches of {BATCH_SIZE}...")
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        with driver.session() as session:
            import_batch(session, batch)

        elapsed = time.time() - start_time
        rate = (i + len(batch)) / elapsed if elapsed > 0 else 0
        pct = ((i + len(batch)) / total) * 100

        print(
            f"   Batch {batch_num}/{total_batches} | "
            f"{i + len(batch):,}/{total:,} ({pct:.1f}%) | "
            f"{rate:.0f} movies/sec | "
            f"Elapsed: {elapsed:.1f}s"
        )

    total_time = time.time() - start_time
    print(f"\n✅ Import complete in {total_time:.1f} seconds!\n")

    # Step 4: Verify counts
    print("📊 Step 4: Verifying graph statistics...")
    with driver.session() as session:
        stats = session.run("""
            MATCH (m:Movie) WITH count(m) AS movies
            MATCH (d:Director) WITH movies, count(d) AS directors
            MATCH (a:Actor) WITH movies, directors, count(a) AS actors
            MATCH (g:Genre) WITH movies, directors, actors, count(g) AS genres
            MATCH (c:Country) WITH movies, directors, actors, genres, count(c) AS countries
            MATCH (l:Language) WITH movies, directors, actors, genres, countries, count(l) AS languages
            MATCH (dec:Decade) WITH movies, directors, actors, genres, countries, languages, count(dec) AS decades
            MATCH (sp:StreamingPlatform) WITH movies, directors, actors, genres, countries, languages, decades, count(sp) AS platforms
            RETURN movies, directors, actors, genres, countries, languages, decades, platforms
        """).single()

        print(f"   🎬 Movies:              {stats['movies']:,}")
        print(f"   🎥 Directors:            {stats['directors']:,}")
        print(f"   🌟 Actors:               {stats['actors']:,}")
        print(f"   🎭 Genres:               {stats['genres']:,}")
        print(f"   🌍 Countries:            {stats['countries']:,}")
        print(f"   🗣️  Languages:            {stats['languages']:,}")
        print(f"   📅 Decades:              {stats['decades']:,}")
        print(f"   📺 Streaming Platforms:  {stats['platforms']:,}")

        # Count relationships
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS rels").single()
        print(f"   🔗 Total Relationships:  {rel_count['rels']:,}")

    print()
    print("=" * 60)
    print("  ✅ CineGraph AI graph is ready!")
    print("  Next: Configure your agent in the Aura Console.")
    print("  See AGENT_CONFIG.md for system prompt & tools.")
    print("=" * 60)

    driver.close()


if __name__ == "__main__":
    main()
