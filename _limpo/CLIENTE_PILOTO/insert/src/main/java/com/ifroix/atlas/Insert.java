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
class EmpEntity {
    @Id
    @Column(name = "EMP_NO")
    private Integer empNo;

    @Column(name = "EMP_NAME")
    private String empName;

    @Column(name = "EMP_SALARY")
    private BigDecimal empSalary;

    public EmpEntity(Integer empNo, String empName, BigDecimal empSalary) {
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
class Insert {
    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        for (int idx = 1; idx <= 10; idx++) {
            Integer empNo = idx;
            String empName = "Employee" + idx;
            BigDecimal empSalary = new BigDecimal(idx * 1000);
            EmpEntity entity = new EmpEntity(empNo, empName, empSalary);
            // repository.save(entity);
        }
    }
}