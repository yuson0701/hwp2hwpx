import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import kr.dogfoot.hwplib.object.HWPFile;
import kr.dogfoot.hwplib.object.bindata.EmbeddedBinaryData;
import kr.dogfoot.hwplib.org.apache.poi.poifs.filesystem.*;
import kr.dogfoot.hwplib.reader.HWPReader;

/** Synthetic documents only: no user document data is included. */
public class BinDataRegression {
    private static void little(ByteArrayOutputStream out, int value, int bytes) {
        for (int i = 0; i < bytes; i++) out.write(value >>> (i * 8));
    }

    private static byte[] deflate(byte[] data) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        Deflater compressor = new Deflater(6, true);
        try (DeflaterOutputStream stream = new DeflaterOutputStream(out, compressor)) {
            stream.write(data);
        } finally {
            compressor.end();
        }
        return out.toByteArray();
    }

    private static byte[] record(int id, int mode) {
        ByteArrayOutputStream payload = new ByteArrayOutputStream();
        little(payload, 1 | (mode << 4), 2); // embedding + compression mode
        little(payload, id, 2);
        little(payload, 3, 2);
        byte[] extension = "png".getBytes(StandardCharsets.UTF_16LE);
        payload.write(extension, 0, extension.length);
        ByteArrayOutputStream record = new ByteArrayOutputStream();
        little(record, 18 | (payload.size() << 20), 4); // HWPTAG_BIN_DATA
        byte[] bytes = payload.toByteArray();
        record.write(bytes, 0, bytes.length);
        return record.toByteArray();
    }

    public static void main(String[] args) throws Exception {
        // A valid one-pixel PNG, with no external content.
        byte[] png = Base64.getDecoder().decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=");
        boolean compressed = Boolean.parseBoolean(args[1]);
        boolean ordered = Boolean.parseBoolean(args[2]);
        int[] ids = ordered ? new int[]{1, 2, 3} : new int[]{3, 1, 7};
        int[] modes = {2, 1, 0}; // raw, explicit deflate, storage default
        POIFSFileSystem fs = new POIFSFileSystem();
        byte[] header = new byte[256];
        byte[] signature = "HWP Document File".getBytes(StandardCharsets.US_ASCII);
        System.arraycopy(signature, 0, header, 0, signature.length);
        header[32] = 3; header[34] = 0; header[35] = 5;
        header[36] = (byte)(compressed ? 1 : 0);
        fs.createDocument(new ByteArrayInputStream(header), "FileHeader");
        fs.createDirectory("BodyText");
        DirectoryEntry binData = fs.createDirectory("BinData");
        ByteArrayOutputStream info = new ByteArrayOutputStream();
        for (int i = 0; i < ids.length; i++) {
            info.write(record(ids[i], modes[i]));
            boolean zipped = modes[i] == 1 || (modes[i] == 0 && compressed);
            byte[] data = zipped ? deflate(png) : png;
            binData.createDocument(String.format("BIN%04X.png", ids[i]), new ByteArrayInputStream(data));
        }
        byte[] docInfo = info.toByteArray();
        fs.createDocument(new ByteArrayInputStream(compressed ? deflate(docInfo) : docInfo), "DocInfo");
        try (OutputStream output = Files.newOutputStream(Paths.get(args[0]))) {
            fs.writeFilesystem(output);
        }
        HWPFile parsed = HWPReader.fromFile(args[0]);
        if (parsed.getBinData().getEmbeddedBinaryDataList().size() != ids.length) {
            throw new AssertionError("Missing embedded images");
        }
        for (EmbeddedBinaryData image : parsed.getBinData().getEmbeddedBinaryDataList()) {
            if (!Arrays.equals(png, image.getData())) {
                throw new AssertionError("Image bytes changed: " + image.getName());
            }
        }
        System.out.println("All image bytes preserved");
    }
}
