package com.ifroix.atlas;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;
import java.math.BigDecimal;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Entity
@Table(name = "EMP")
class EmployeeEntity {
    @Id
    @Column(name = "EMP_NO")
    private Integer empNo;

    @Column(name = "EMP_NAME")
    private String empName;

    @Column(name = "EMP_SALARY")
    private BigDecimal empSalary;

    public EmployeeEntity(Integer empNo, String empName, BigDecimal empSalary) {
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

    public BigDecimal getEmpSalary() {
        return empSalary;
    }
}

@Service
class DeclareBindVar {
    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        EmployeeEntity entity = new EmployeeEntity(1, "John Doe", new BigDecimal("50000.00"));
        // repository.save(entity);
    }
}