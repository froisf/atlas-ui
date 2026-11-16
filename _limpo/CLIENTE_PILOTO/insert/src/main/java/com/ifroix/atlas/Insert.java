package com.ifroix.atlas;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;

@Service
class CommitRollback {
    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        // Setup DB
        // Inicialização de variáveis
        Integer testNo = 1; // TEST-NO
        String testName = "John Doe"; // TEST-NAME
        Integer testSalary = 5000; // TEST-SALARY
        Integer empNo = 1; // EMP-NO
        String empName = "Jane Smith"; // EMP-NAME
        Integer empSalary = 6000; // EMP-SALARY
        Integer idx = 1; // IDX
        Integer logCount = 1000; // LOG-COUNT

        // INSERT ROWS USING HOST VARIABLE
        EmployeeEntity entity = new EmployeeEntity(empNo, empName, new BigDecimal(empSalary));
        // repository.save(entity);

        // COMMIT
        // O Spring gerencia COMMIT automaticamente aqui

        // DELETE
        // Lógica para deletar a entidade
        // repository.delete(entity);

        // ROLLBACK
        // O Spring gerencia ROLLBACK automaticamente aqui se ocorrer uma exceção

        // SHOW RESULT
        // Lógica para mostrar o resultado

        // CLEANUP-DB
        // Lógica para limpar o banco de dados
    }

    // EmployeeEntity
    class EmployeeEntity {
        private Integer empId;
        private String empName;
        private BigDecimal empSalary;

        public EmployeeEntity(Integer empId, String empName, BigDecimal empSalary) {
            this.empId = empId;
            this.empName = empName;
            this.empSalary = empSalary;
        }

        public Integer getEmpId() {
            return empId;
        }

        public String getEmpName() {
            return empName;
        }

        public BigDecimal getEmpSalary() {
            return empSalary;
        }
    }
}