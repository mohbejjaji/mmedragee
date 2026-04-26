import psycopg2
from psycopg2.extras import DictCursor
from urllib.parse import quote_plus
from sqlalchemy import create_engine

class CursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None
        
    def execute(self, sql, params=()):
        if isinstance(params, (list, tuple)):
            if '?' in sql:
                # Simple replace '?' to '%s' 
                # Note: handle cases where '?' might be in quotes if it occurs, but typical queries don't have this.
                sql = sql.replace('?', '%s')
            
            import numpy as np
            new_params = []
            for p in params:
                if isinstance(p, np.integer):
                    new_params.append(int(p))
                elif isinstance(p, np.floating):
                    new_params.append(float(p))
                elif isinstance(p, np.bool_):
                    new_params.append(bool(p))
                else:
                    new_params.append(p)
            params = tuple(new_params)
            
        self.cursor.execute(sql, params)
        
        if sql.lstrip().upper().startswith("INSERT"):
            try:
                self.cursor.execute("SELECT LASTVAL()")
                last_id = self.cursor.fetchone()[0]
                self.lastrowid = last_id
            except Exception:
                pass
        return self
        
    def fetchall(self): return self.cursor.fetchall()
    def fetchmany(self, size=None): return self.cursor.fetchmany(size)
    def fetchone(self): return self.cursor.fetchone()
    def close(self): self.cursor.close()

    @property
    def description(self):
        return self.cursor.description
        
    def __iter__(self):
        return iter(self.cursor)

class SupabaseAdapter:
    def __init__(self):
        import streamlit as st
        # Utiliser .get pour éviter un crash immédiat si le secret est manquant
        self.dsn = st.secrets.get("DB_URL")
        
        if not self.dsn:
            st.error("### 🛡️ Sécurité : Configuration Manquante")
            st.warning("""
            Le secret `DB_URL` est manquant dans votre configuration. 
            
            **Pour corriger cela sur Streamlit Cloud :**
            1. Allez dans les **Settings** de votre application sur le dashboard Streamlit.
            2. Ouvrez l'onglet **Secrets**.
            3. Ajoutez la ligne suivante (avec vos vrais identifiants) :
               `DB_URL = "votre_url_de_base_de_donnees"`
            4. Enregistrez.
            """)
            st.info("💡 **Note de sécurité** : Ne remettez pas vos mots de passe dans le fichier `secrets.toml` sur GitHub.")
            st.stop()
            
        try:
            self.pg_conn = psycopg2.connect(self.dsn, cursor_factory=DictCursor)
            self.engine = create_engine(self.dsn)
        except Exception as e:
            st.error(f"❌ Erreur de connexion à la base de données : {e}")
            st.stop()
            
        self.row_factory = None

    def cursor(self):
        return CursorWrapper(self.pg_conn.cursor())

    def execute(self, sql, params=()):
        c = self.cursor()
        c.execute(sql, params)
        return c

    def commit(self):
        self.pg_conn.commit()

    def rollback(self):
        self.pg_conn.rollback()

    def close(self):
        self.pg_conn.close()
        self.engine.dispose()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
            
    def __getattr__(self, name):
        # Fallback to engine so pandas could theoretically use it, even though pandas does ducktyping
        return getattr(self.engine, name)
