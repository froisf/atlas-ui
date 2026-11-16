package com.ifroix.atlas;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;

class InsertTest {
    @Test
    void testExecutarLogica() {
        Insert obj = new Insert();
        assertDoesNotThrow(() -> obj.executarLogica());
    }
}