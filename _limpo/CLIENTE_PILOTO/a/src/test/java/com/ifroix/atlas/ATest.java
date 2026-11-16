package com.ifroix.atlas;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;

@SpringBootTest
public class ATest {
    @Autowired
    private A a;

    @Test
    public void testExecutarLogica() {
        assertDoesNotThrow(() -> a.executarLogica());
    }
}