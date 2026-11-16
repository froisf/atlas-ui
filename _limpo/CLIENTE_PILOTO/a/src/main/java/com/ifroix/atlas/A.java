package com.ifroix.atlas;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class A {

    public void executarLogica() {
        System.out.println("HELLO, ATLAS AGENTIC!");
    }
}