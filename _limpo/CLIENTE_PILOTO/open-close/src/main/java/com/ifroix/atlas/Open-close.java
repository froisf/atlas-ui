package com.ifroix.atlas;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import java.math.BigDecimal;

@Service
class OpenClose {
    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        // Implementação do fluxo baseado no JSON IR
        // SETUP-DB
        // OPEN CURSOR1
        // DISPLAY-TEST-RESULT
        // CLOSE CURSOR1
        // DISPLAY-TEST-RESULT
        // CLEANUP-DB

        // Exemplo de como inserir um funcionário
        Integer empNo = 12345;
        String empName = "John Doe";
        BigDecimal empSalary = new BigDecimal("50000.00");
        EmployeeEntity employeeEntity = new EmployeeEntity(empNo, empName, empSalary);
        // repository.save(employeeEntity);
    }
}

@Entity
@Table(name = "EMPLOYEE")
class EmployeeEntity {
    @Id
    @Column(name = "EMP_ID")
    private Integer empId;

    @Column(name = "EMP_NAME")
    private String empName;

    @Column(name = "EMP_SALARY")
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