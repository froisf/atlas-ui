package com.ifroix.atlas;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class Test {

    public void executarLogica() {
        Integer wsCounter = 0;
        String wsName = "Hello";
        boolean wsFlag = false;

        System.out.println(wsName);

        while (wsCounter < 10) {
            wsCounter++;
            if (!wsFlag) {
                System.out.println("Flag is zero");
            }
            if (wsCounter == 0) {
                System.out.println("Counter is zero");
            } else {
                System.out.println("Counter is not zero");
            }
        }
    }
}