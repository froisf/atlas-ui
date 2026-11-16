package com.ifroix.atlas;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import java.math.BigDecimal;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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
        this.empId = empId; this.empName = empName; this.empSalary = empSalary;
    }
    public Integer getEmpId() { return empId; }
    public String getEmpName() { return empName; }
    public BigDecimal getEmpSalary() { return empSalary; }
}

@Service
class Insert {
    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        for (int idx = 1; idx <= 10; idx++) {
            Integer empId = idx; // Assuming TEST-NO is a sequence from 1 to 10
            String empName = "Employee" + idx; // Assuming TEST-NAME is a sequence of names
            BigDecimal empSalary = new BigDecimal(idx * 1000); // Assuming TEST-SALARY is a sequence of salaries
            EmployeeEntity entity = new EmployeeEntity(empId, empName, empSalary);
            // repository.save(entity);
        }
    }
}