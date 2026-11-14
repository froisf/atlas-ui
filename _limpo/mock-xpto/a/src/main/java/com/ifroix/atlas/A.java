package com.ifroix.atlas;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class A {

    public void executarLogica() {
        String programId = "HELLO-WORLD";
        String nome = "nulo";
        String tipo = "nulo";
        List<String> fluxo = List.of("DISPLAY", "STOP RUN");

        System.out.println("Program ID: " + programId);
        System.out.println("Nome: " + nome);
        System.out.println("Tipo: " + tipo);
        System.out.println("Fluxo: " + fluxo);
    }
}