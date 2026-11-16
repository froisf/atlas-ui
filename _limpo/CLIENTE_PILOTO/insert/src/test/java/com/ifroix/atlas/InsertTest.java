package com.ifroix.atlas;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Assertions;

class InsertTest {
    @Test
    void testExecutarLogica() {
        Insert obj = new Insert();
        Assertions.assertDoesNotThrow(() -> obj.executarLogica());
    }
}