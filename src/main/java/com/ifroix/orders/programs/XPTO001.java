import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Scanner;

public class Main {

    public static void main(String[] args) {
        // Crie um arquivo de entrada e saída
        String inputFile = "input.txt";
        String outputFile = "output.txt";

        // Abra os arquivos de entrada e saída
        File inputfile = new File(inputFile);
        File outputfile = new File(outputFile);

        try {
            Scanner scanner = new Scanner(inputfile);
            FileWriter writer = new FileWriter(outputfile);

            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                // Escreva a linha no arquivo de saída
                writer.write(line + System.lineSeparator());
            }
            scanner.close();
            writer.close();
        } catch (FileNotFoundException e) {
            System.out.println("Arquivo não encontrado: " + e.getMessage());
        } catch (IOException e) {
            System.out.println("Erro ao escrever no arquivo: " + e.getMessage());
        }
    }
}