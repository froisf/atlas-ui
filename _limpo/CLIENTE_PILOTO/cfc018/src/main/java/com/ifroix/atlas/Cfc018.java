package com.ifroix.atlas;

import java.math.BigDecimal;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
class Cfc018 {

    @Transactional(rollbackFor = Exception.class)
    public void executarLogica() {
        // Simulando a seleção de itens de pedido
        OrderItemsEntity orderItemsEntity = new OrderItemsEntity(1, "Item 1", new BigDecimal("10.50"));
        // Aqui você pode adicionar lógica para chamar o serviço que simula o CALL '[STRING_MASKED]' USING WS-ORDER-REC
        // E também a lógica para exibir '[STRING_MASKED]'
        // Exemplo de como isso poderia ser feito:
        // orderItemsService.callMaskedService(orderItemsEntity);
        // System.out.println("[STRING_MASKED]");
    }
}

// Simulando a entidade OrderItemsEntity
class OrderItemsEntity {
    private Integer orderId;
    private String itemName;
    private BigDecimal totalAmt;

    public OrderItemsEntity(Integer orderId, String itemName, BigDecimal totalAmt) {
        this.orderId = orderId;
        this.itemName = itemName;
        this.totalAmt = totalAmt;
    }

    public Integer getOrderId() {
        return orderId;
    }

    public String getItemName() {
        return itemName;
    }

    public BigDecimal getTotalAmt() {
        return totalAmt;
    }
}