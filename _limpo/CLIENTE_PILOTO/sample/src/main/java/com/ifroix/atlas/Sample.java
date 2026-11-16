package com.ifroix.atlas;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

@Service
class Sample {

    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        // Simulando a conexão com o banco de dados
        String dbName = "<|DB_NAME|>@<|DB_HOST|>:<|DB_PORT|>";
        String username = "<|DB_USER|>";
        String password = "<|DB_PASSWORD|>";

        // Criando a entidade EmployeeEntity
        class EmployeeEntity {
            @jakarta.persistence.Id
            private Integer empNo;

            private String empName;

            private Integer empSalary;

            public EmployeeEntity(Integer empNo, String empName, Integer empSalary) {
                this.empNo = empNo;
                this.empName = empName;
                this.empSalary = empSalary;
            }

            public Integer getEmpNo() {
                return empNo;
            }

            public String getEmpName() {
                return empName;
            }

            public Integer getEmpSalary() {
                return empSalary;
            }
        }

        // Criando o repositório
        interface EmployeeRepository {
            void save(EmployeeEntity entity);
        }

        // Implementação simulada do repositório
        class EmployeeRepositoryImpl implements EmployeeRepository {
            @Override
            public void save(EmployeeEntity entity) {
                // Simulação de inserção no banco de dados
                System.out.println("Inserindo registro: " + entity.getEmpNo() + ", " + entity.getEmpName() + ", " + entity.getEmpSalary());
            }
        }

        // Inserindo registros iniciais
        EmployeeRepository repository = new EmployeeRepositoryImpl();
        repository.save(new EmployeeEntity(46, "[STRING_MASKED]", -320));
        repository.save(new EmployeeEntity(47, "[STRING_MASKED]", 480));

        // Inserindo 10 registros adicionais
        for (int idx = 1; idx <= 10; idx++) {
            Integer empNo = idx; // Simulando TEST-NO
            String empName = "[STRING_MASKED]"; // Simulando TEST-NAME
            Integer empSalary = idx; // Simulando TEST-SALARY
            repository.save(new EmployeeEntity(empNo, empName, empSalary));
        }
    }
}