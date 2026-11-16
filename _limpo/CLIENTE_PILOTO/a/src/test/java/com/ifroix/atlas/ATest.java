package com.ifroix.atlas;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;

public class ATest {
    @Test
    public void testExecutarLogica() {
        A obj = new A();
        Assertions.assertDoesNotThrow(() -> obj.executarLogica());
    }
}