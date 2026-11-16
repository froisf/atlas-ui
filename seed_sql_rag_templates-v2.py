import chromadb

def seed_rag_v2():
    print("⏳ Inicializando ChromaDB para RAG SQL (v2)...")
    client = chromadb.PersistentClient(path="./chroma_db")
    try: client.delete_collection("sql_rag_templates")
    except: pass
    collection = client.create_collection("sql_rag_templates")
    
    templates = [
        {
            "id": "DB2_ENTITY_JPA",
            "cobol": "01 EMPLOYEE-REC. 05 EMP-ID PIC S9(04) COMP. 05 EMP-NAME PIC X(20). 05 EMP-SALARY PIC S9(15)V99 COMP-3.",
            "ir": "{\"operation\": \"ENTITY_DEFINITION\", \"table\": \"EMPLOYEE\", \"columns\": [{\"name\": \"EMP_ID\", \"type\": \"Integer\"}, {\"name\": \"EMP_NAME\", \"type\": \"String\"}, {\"name\": \"EMP_SALARY\", \"type\": \"BigDecimal\"}]}",
            "java": "package com.ifroix.atlas.entity;\n\nimport jakarta.persistence.Entity;\nimport jakarta.persistence.Id;\nimport jakarta.persistence.Table;\nimport jakarta.persistence.Column;\nimport java.math.BigDecimal;\n\n@Entity\n@Table(name = \"EMPLOYEE\")\nclass EmployeeEntity {\n    @Id\n    @Column(name = \"EMP_ID\")\n    private Integer empId;\n\n    @Column(name = \"EMP_NAME\")\n    private String empName;\n\n    @Column(name = \"EMP_SALARY\")\n    private BigDecimal empSalary;\n\n    public EmployeeEntity(Integer empId, String empName, BigDecimal empSalary) {\n        this.empId = empId; this.empName = empName; this.empSalary = empSalary;\n    }\n    public Integer getEmpId() { return empId; }\n    public String getEmpName() { return empName; }\n    public BigDecimal getEmpSalary() { return empSalary; }\n}"
        },
        {
            "id": "DB2_INSERT",
            "cobol": "EXEC SQL INSERT INTO EMPLOYEE (EMP_ID, EMP_NAME, SALARY) VALUES (:EMP-ID, :EMP-NAME, :SALARY) END-EXEC.",
            "ir": "{\"operation\": \"DATA_INSERT\", \"entity\": \"EmployeeEntity\", \"transactional\": true}",
            "java": "package com.ifroix.atlas.service;\n\nimport org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;\nimport java.math.BigDecimal;\n\n@Service\nclass EmployeeService {\n    @Transactional\n    public void insertEmployee(Integer empId, String empName, BigDecimal salary) {\n        EmployeeEntity entity = new EmployeeEntity(empId, empName, salary);\n        // repository.save(entity);\n    }\n}"
        },
        {
            "id": "DB2_COMMIT_ROLLBACK",
            "cobol": "EXEC SQL COMMIT END-EXEC. EXEC SQL ROLLBACK END-EXEC.",
            "ir": "{\"operation\": \"TRANSACTION_CONTROL\", \"transactional\": true, \"rollback\": true}",
            "java": "package com.ifroix.atlas.service;\n\nimport org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;\n\n@Service\nclass TransactionService {\n    @Transactional(rollbackFor = Exception.class)\n    public void executeTransaction() {\n        // O Spring gerencia COMMIT e ROLLBACK automaticamente aqui\n    }\n}"
        }
    ]
    
    for t in templates:
        doc = f"COBOL: {t['cobol']}\nIR: {t['ir']}\nJAVA: {t['java']}"
        collection.add(documents=[doc], metadatas=[{"pattern_id": t["id"], "payload_json": t["java"]}], ids=[t["id"]])
    print(f"✅ {len(templates)} templates RAG v2 (com COMMIT/ROLLBACK) carregados!")

if __name__ == "__main__": seed_rag_v2()
