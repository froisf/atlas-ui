import chromadb
import json
import sys

def seed_rag():
    print("⏳ Inicializando ChromaDB para RAG SQL...")
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Remove a coleção se já existir para evitar duplicatas no teste
    try:
        client.delete_collection("sql_rag_templates")
    except:
        pass
        
    collection = client.create_collection("sql_rag_templates")
    
    templates = [
        {
            "id": "DB2_SELECT_CURSOR",
            "cobol": "EXEC SQL DECLARE C1 CURSOR FOR SELECT EMP_ID, SALARY FROM EMPLOYEE WHERE DEPT = :HOST-DEPT END-EXEC. EXEC SQL OPEN C1 END-EXEC. EXEC SQL FETCH C1 INTO :EMP-ID, :SALARY END-EXEC.",
            "ir": "{\"operation\": \"DATA_ACCESS_QUERY\", \"entity\": \"Employee\", \"params\": [{\"name\": \"dept\", \"type\": \"String\"}], \"returns\": [{\"name\": \"empId\", \"type\": \"String\"}, {\"name\": \"salary\", \"type\": \"BigDecimal\"}], \"transactional\": false}",
            "java": "package com.ifroix.atlas.repository;\n\nimport org.springframework.data.jpa.repository.JpaRepository;\nimport org.springframework.data.jpa.repository.Query;\nimport org.springframework.data.repository.query.Param;\nimport org.springframework.stereotype.Repository;\nimport java.math.BigDecimal;\nimport java.util.List;\n\n@Repository\npublic interface EmployeeRepository extends JpaRepository<EmployeeEntity, String> {\n    @Query(\"SELECT e FROM EmployeeEntity e WHERE e.dept = :dept\")\n    List<EmployeeProjection> findSalaryByDept(@Param(\"dept\") String dept);\n}"
        },
        {
            "id": "DB2_COMMIT_ROLLBACK",
            "cobol": "EXEC SQL COMMIT END-EXEC. EXEC SQL ROLLBACK END-EXEC.",
            "ir": "{\"operation\": \"TRANSACTION_CONTROL\", \"transactional\": true, \"rollback\": true}",
            "java": "package com.ifroix.atlas.service;\n\nimport org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;\n\n@Service\npublic class TransactionService {\n    @Transactional(rollbackFor = Exception.class)\n    public void executeTransaction() {\n        // Lógica de negócio com commit/rollback automático\n    }\n}"
        },
        {
            "id": "DB2_INSERT",
            "cobol": "EXEC SQL INSERT INTO EMPLOYEE (EMP_ID, SALARY) VALUES (:EMP-ID, :SALARY) END-EXEC.",
            "ir": "{\"operation\": \"DATA_INSERT\", \"entity\": \"Employee\", \"transactional\": true}",
            "java": "package com.ifroix.atlas.service;\n\nimport org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;\nimport java.math.BigDecimal;\n\n@Service\npublic class EmployeeService {\n    private final EmployeeRepository repository;\n\n    public EmployeeService(EmployeeRepository repository) {\n        this.repository = repository;\n    }\n\n    @Transactional\n    public void insertEmployee(String empId, BigDecimal salary) {\n        EmployeeEntity entity = new EmployeeEntity(empId, salary);\n        repository.save(entity);\n    }\n}"
        },
        {
            "id": "DB2_UPDATE_DELETE",
            "cobol": "EXEC SQL UPDATE EMPLOYEE SET SALARY = :NEW-SALARY WHERE EMP_ID = :EMP-ID END-EXEC. EXEC SQL DELETE FROM EMPLOYEE WHERE EMP_ID = :EMP-ID END-EXEC.",
            "ir": "{\"operation\": \"DATA_UPDATE_DELETE\", \"entity\": \"Employee\", \"transactional\": true}",
            "java": "package com.ifroix.atlas.repository;\n\nimport org.springframework.data.jpa.repository.JpaRepository;\nimport org.springframework.data.jpa.repository.Modifying;\nimport org.springframework.data.jpa.repository.Query;\nimport org.springframework.data.repository.query.Param;\nimport org.springframework.stereotype.Repository;\nimport org.springframework.transaction.annotation.Transactional;\nimport java.math.BigDecimal;\n\n@Repository\npublic interface EmployeeRepository extends JpaRepository<EmployeeEntity, String> {\n    @Modifying\n    @Transactional\n    @Query(\"UPDATE EmployeeEntity e SET e.salary = :salary WHERE e.empId = :empId\")\n    void updateSalary(@Param(\"empId\") String empId, @Param(\"salary\") BigDecimal salary);\n\n    @Modifying\n    @Transactional\n    @Query(\"DELETE FROM EmployeeEntity e WHERE e.empId = :empId\")\n    void deleteByEmpId(@Param(\"empId\") String empId);\n}"
        },
        {
            "id": "DB2_CONNECT_DISCONNECT",
            "cobol": "EXEC SQL CONNECT TO :DB-NAME END-EXEC. EXEC SQL DISCONNECT END-EXEC.",
            "ir": "{\"operation\": \"CONNECTION_MANAGEMENT\", \"connection_pool\": \"HikariCP\"}",
            "java": "package com.ifroix.atlas.config;\n\nimport org.springframework.context.annotation.Configuration;\nimport com.zaxxer.hikari.HikariConfig;\nimport com.zaxxer.hikari.HikariDataSource;\nimport javax.sql.DataSource;\n\n@Configuration\npublic class DatabaseConfig {\n    // O Spring Boot gerencia a conexão e desconexão automaticamente via HikariCP\n    public DataSource dataSource() {\n        HikariConfig config = new HikariConfig();\n        config.setJdbcUrl(\"jdbc:db2://localhost:50000/mydb\");\n        return new HikariDataSource(config);\n    }\n}"
        }
    ]
    
    for t in templates:
        # Cria o documento que será vetorizado
        doc = f"COBOL: {t['cobol']}\nIR: {t['ir']}\nJAVA: {t['java']}"
        
        collection.add(
            documents=[doc],
            metadatas=[{"pattern_id": t["id"], "cobol_clause": t["cobol"][:50], "payload_json": t["java"]}],
            ids=[t["id"]]
        )
        
    print(f"✅ {len(templates)} templates RAG carregados com sucesso na coleção 'sql_rag_templates'!")

if __name__ == "__main__":
    seed_rag()
