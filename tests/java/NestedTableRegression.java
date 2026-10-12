import kr.dogfoot.hwplib.object.HWPFile;
import kr.dogfoot.hwplib.object.bodytext.paragraph.Paragraph;
import kr.dogfoot.hwplib.object.bodytext.control.ControlTable;
import kr.dogfoot.hwplib.object.bodytext.control.ControlType;
import kr.dogfoot.hwplib.object.bodytext.control.table.Cell;
import kr.dogfoot.hwplib.tool.blankfilemaker.BlankFileMaker;
import kr.dogfoot.hwplib.tool.blankfilemaker.EmptyParagraphAdder;
import kr.dogfoot.hwplib.writer.HWPWriter;

/** Creates a synthetic nested table with a following outer row. */
public class NestedTableRegression {
    static ControlTable table(Paragraph p, int rows, int id, int depth) throws Exception {
        if(p.getText()==null) p.createText();
        p.getText().addExtendCharForTable();
        ControlTable t = (ControlTable)p.addNewControl(ControlType.Table);
        t.getHeader().setInstanceId(id);
        t.getTable().setRowCount(rows);
        t.getTable().setColumnCount(1);
        for(int r=0;r<rows;r++) {
            t.getTable().addCellCountOfRow(1);
            Cell c=t.addNewRow().addNewCell();
            c.getListHeader().setRowIndex(r);
            c.getListHeader().setColIndex(0);
            c.getListHeader().setRowSpan(1);
            c.getListHeader().setColSpan(1);
            c.getListHeader().setWidth(10000);
            c.getListHeader().setHeight(1000);
            EmptyParagraphAdder.add(c.getParagraphList());
            Paragraph cp=c.getParagraphList().getParagraph(0);
            if(cp.getText()==null) cp.createText();
            cp.getText().addString("table-"+id+"-row-"+r);
            if(r==0 && depth>0) table(cp,2,id+1,depth-1);
        }
        return t;
    }
    public static void main(String[] args) throws Exception {
        HWPFile h=BlankFileMaker.make();
        table(h.getBodyText().getSectionList().get(0).getParagraph(0),3,100, Integer.parseInt(args[1]));
        HWPWriter.toFile(h,args[0]);
    }
}
