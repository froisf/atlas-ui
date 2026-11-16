package com.ifroix.atlas;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import java.math.BigDecimal;

@Service
class Fetch {
    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        String tableName = "EMP";
        String selectQuery = "SELECT EMP_NO, EMP_NAME, EMP_SALARY FROM EMP ORDER BY EMP_NO";
        jdbcTemplate.query(selectQuery, (rs, rowNum) -> {
            Integer empNo = rs.getInt("EMP_NO");
            String empName = rs.getString("EMP_NAME");
            BigDecimal empSalary = new BigDecimal(rs.getString("EMP_SALARY"));
            System.out.println("EMP_NO: " + empNo + ", EMP_NAME: " + empName + ", EMP_SALARY: " + empSalary);
            return null;
        });

        String dropTableQuery = "DROP TABLE IF EXISTS EMP";
        jdbcTemplate.execute(dropTableQuery);
    }
}

class EmployeeEntity {
    private Integer empNo;
    private String empName;
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