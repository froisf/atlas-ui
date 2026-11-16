package com.ifroix.atlas;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
class Select {
    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        // SETUP-DB
        // INSERT ROWS USING HOST VARIABLE
        EmployeeEntity entity = new EmployeeEntity(1, "John Doe", new BigDecimal("50000"));
        // repository.save(entity);

        // COMMIT
        // SELECT * INTO :READ-TBL FROM EMP WHERE EMP_NO > 4
        List<EmployeeEntity> readTbl = new ArrayList<>();
        // readTbl = repository.findByEmpNoGreaterThan(4);

        // OUTPUT-RETURN-CODE-TEST
        int logCount = 0;
        for (EmployeeEntity emp : readTbl) {
            logCount++;
        }

        // DISPLAY READ-NO(IDX), READ-NAME(IDX), READ-SALARY(IDX)
        for (int idx = 0; idx < readTbl.size(); idx++) {
            EmployeeEntity emp = readTbl.get(idx);
            System.out.println("READ-NO(" + (idx + 1) + "): " + emp.getEmpId());
            System.out.println("READ-NAME(" + (idx + 1) + "): " + emp.getEmpName());
            System.out.println("READ-SALARY(" + (idx + 1) + "): " + emp.getEmpSalary());
        }

        // CLEANUP-DB
        // repository.deleteAll();
    }
}

class EmployeeEntity {
    private Integer empId;
    private String empName;
    private BigDecimal empSalary;

    EmployeeEntity(Integer empId, String empName, BigDecimal empSalary) {
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